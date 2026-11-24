#!/usr/bin/env bash
# AirString 本地启动 — 摄像头需安全上下文:
#   桌面: http://localhost:8765 即可
#   手机: https://<本机IP>:8443 (自签证书, 点「高级→继续访问」)
cd "$(dirname "$0")"
exec python3 serve.py "${1:-8765}" "${2:-8443}"
