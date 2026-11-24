#!/usr/bin/env python3
"""AirString 双协议服务器: HTTP(8765) + HTTPS(8443, 自签证书自动生成).

手机摄像头需要安全上下文(https); 桌面 localhost 走 http 即可.
用法: python3 serve.py [http端口] [https端口]
"""
import http.server
import os
import pathlib
import socketserver
import ssl
import subprocess
import sys
import threading

ROOT = pathlib.Path(__file__).parent
CERT = ROOT / '.certs' / 'server.pem'
PORT_HTTP = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
PORT_HTTPS = int(sys.argv[2]) if len(sys.argv) > 2 else 8443


def lan_ips():
    out = subprocess.run(['hostname', '-I'], capture_output=True, text=True).stdout
    return [ip for ip in out.split() if ':' not in ip]  # 只留 IPv4


def ensure_cert():
    if CERT.exists():
        return
    CERT.parent.mkdir(exist_ok=True)
    san = ','.join(['DNS:localhost', 'IP:127.0.0.1'] + [f'IP:{ip}' for ip in lan_ips()])
    subprocess.run([
        'openssl', 'req', '-x509', '-newkey', 'rsa:2048',
        '-keyout', str(CERT), '-out', str(CERT),
        '-days', '3650', '-nodes', '-subj', '/CN=air-string.local',
        '-addext', f'subjectAltName={san}',
        '-addext', 'basicConstraints=CA:FALSE',
        '-addext', 'keyUsage=digitalSignature,keyEncipherment',
        '-addext', 'extendedKeyUsage=serverAuth',
    ], check=True)
    print(f'[cert] 自签证书已生成(10年) {CERT}')
    print(f'[cert] SAN: {san}')
    # 注: EC 曲线在部分受限 openssl 构建上不可用, 故统一走 RSA 2048


class Handler(http.server.SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'  # keep-alive: 慢/抖链路下少握手=少一个断点

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(ROOT), **kw)

    # vendor 静态资源（模型/wasm/bundle）体积大且内容不变 → 允许浏览器长期缓存；
    # 其余（index.html）不缓存，保证改动即时生效。
    def _is_vendor(self, path):
        return path.split('?', 1)[0].split('#', 1)[0].startswith('/vendor/')

    _gz = False  # 本请求是否改送 .gz 版本（translate_path 里判定）

    def setup(self):
        super().setup()
        try:
            self.connection.settimeout(120)  # 单次读写阻塞>120s 判死连接, 线程自行退出
        except Exception:
            pass

    def guess_type(self, path):
        # gzip 分支: translate_path 返回了 .gz 路径, 但 Content-Type 必须按原始扩展名给
        # (动态 import 强制校验 JS MIME, 返回 application/gzip 会被 Chrome 拒收)
        if path.endswith('.gz'):
            path = path[:-3]
        return super().guess_type(path)

    def translate_path(self, path):
        self._gz = False
        p = path.split('?', 1)[0].split('#', 1)[0]
        if self._is_vendor(p) and 'gzip' in self.headers.get('Accept-Encoding', ''):
            gz = super().translate_path(p + '.gz')
            if os.path.isfile(gz):
                self._gz = True
                return gz
        return super().translate_path(path)

    def end_headers(self):
        if self._is_vendor(self.path):
            self.send_header('Cache-Control', 'public, max-age=31536000, immutable')
        else:
            self.send_header('Cache-Control', 'no-store')
        if self._gz:
            self.send_header('Content-Encoding', 'gzip')
        super().end_headers()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    ssl_ctx = None  # HTTPS 实例注入; 握手改在工作线程内完成

    def finish_request(self, request, client_address):
        if self.ssl_ctx is not None:
            # 关键: 不在监听 socket 上包 SSL —— 那样握手发生在 accept 循环里,
            # 一个僵死握手(慢客户端半开连接)会冻结整个服务, 后续连接全部被丢。
            # 在 worker 线程内握手 + 30s 超时, 坏连接只死自己。
            request.settimeout(30)
            request = self.ssl_ctx.wrap_socket(request, server_side=True)
        super().finish_request(request, client_address)


def main():
    ensure_cert()
    httpd = Server(('', PORT_HTTP), Handler)
    httpsd = Server(('', PORT_HTTPS), Handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(CERT))
    httpsd.ssl_ctx = ctx  # 不 wrap 监听 socket: 握手在 worker 线程(Server.finish_request)

    ips = ', '.join(lan_ips()) or '<本机IP>'
    print(f'[http ] http://localhost:{PORT_HTTP}  (桌面鼠标模式 / 摄像头也可, localhost 属安全上下文)')
    print(f'[https] https://{ips}:{PORT_HTTPS}  (手机摄像头用这个 — 自签证书需「高级→继续访问」)')
    threading.Thread(target=httpsd.serve_forever, daemon=True).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
