# 01 · 架构与交互规格

## 来源与定位

- 概念源：X 推文（@EmonData 2026-11 转评 Hashem 的 "Music Maker"）→ 原项目 `Hashem-Al-Ghaili/music-maker`（单 HTML 文件，无 LICENSE）
- 本项目：**净室实现**——只对齐"概念与功能面"，未复制原项目任何代码；并在三处做了实质改进：全离线 vendor、设置持久化、自动化验收 API
- 溯源详情见 `03-provenance.md`

## 技术栈

| 层 | 选型 | 说明 |
|----|------|------|
| 手部追踪 | @mediapipe/tasks-vision 0.10.14（本地 vendor） | HandLandmarker，VIDEO 模式，2 手 × 21 关键点，GPU delegate 失败自动可回 CPU |
| 坐标系 | 视口像素统一坐标系 | 视频归一化坐标经 `VideoMap`（object-fit: cover 等效映射 + 水平镜像）转视口 px；鼠标/触摸原生即视口 px |
| 音频 | Web Audio API | 全合成，无采样；AudioContext 在用户手势中创建 |
| UI | 原生 DOM 面板 + Canvas 叠层 | 面板交互摄像头模式走 elementFromPoint 命中 + 悬停/捏合，鼠标模式走原生事件 |

## 文件结构

```
air-instrument/
├── index.html              # 全部应用（单文件，~1450 行）
├── serve.sh                # 本地服务器（摄像头需 localhost 安全上下文）
├── README.md
├── docs/                   # 本目录
└── vendor/mediapipe/       # 离线运行时（Apache-2.0）
    ├── vision_bundle.js    # ES module 入口
    ├── hand_landmarker.task# float16 模型 7.8MB
    ├── LICENSE.tasks-vision
    └── wasm/               # SIMD / nosimd 双份 wasm 加载器
```

## 交互模型（手势状态机）

```
鼠标 / 触摸模式（Pointer Events 统一, 触屏无悬停, 手势必须显式拆分）:
  演奏   任意划动过弦即拨奏（无需按下; 按住划过同样拨奏）
  画弦   仅「＋画弦」武装态可用（按钮/快捷键N）: 空白按下拖动→松手成弦→自动解除
         — v1.0 曾允许空白处直接拖拽成弦, 触屏上与划弦手势冲突(误建弦), v1.1 移除
  菜单   对徽章"点按"才弹: 位移<12px 且 <400ms
         — v1.0 的徽章命中圆以弦中点为圆心(压在弦上, 可见芯片却画在上方16px),
           扫弦必中导致菜单乱弹; v1.1 改为与可见芯片严格重合的矩形命中
  端点   按住端点圆圈拖动(按住+移动, 与点按天然区分)
```

摄像头模式（每帧 rAF）:
  HandTracker.detect() ──> updateCamHands()
      │ 每手: 捏合比 = |L4-L8| / |L0-L9| / 灵敏度
      │ 滞回: ratio < 0.55 触发捏合, > 0.80 才松开（防抖）
      ▼
  CamGesture.update()
      双手捏合          -> preview 弦（虚线预览）
      预览中任一手松开   -> 长度≥110px 成弦（弹出乐器面板），否则丢弃
      单手捏合+命中端点  -> 拖动端点（<60px 删除）
      单手捏合+命中徽章  -> 打开徽章面板
      其余              -> UI.probeDwell（面板悬停 0.7s / 捏合上升沿选中）
  checkPlucks()
      5 指尖 × 每根弦: 帧间位移线段 straddle 跨越检测
      速度<3px/帧忽略; 力度=speed/40 截断[0.3,1]; 同指尖 70ms 冷却
```

## 关键设计决策

0. **安全上下文与摄像头**：`getUserMedia` 仅在安全上下文可用——`https://*` 或 `http://localhost`。手机经局域网 IP 访问 http 一律拿不到授权（浏览器不弹窗）。方案：`serve.py` 双协议监听（HTTP 8765 + HTTPS 8443 自签证书，SAN 覆盖本机全部 IPv4）；页面加载即检测 `isSecureContext`，非安全上下文直接在启动卡显示分平台指引。
1. **坐标统一到视口像素**：视频坐标、手关键点、弦、鼠标全部在同一空间，避免跨空间换算 bug（开发中实际踩过：首版混用归一化与像素导致拨奏判定失效）。
2. **捏合滞回（hysteresis）**：触发/恢复阈值分离（0.55/0.80），消抖——推文评论区抱怨原版"太灵敏误触/又像树懒慢半拍"，滞回+灵敏度滑条是对此的直接回应。
3. **Karplus-Strong 预计算 + LRU 缓存**：拨弦音色按 (频率×亮度×阻尼×力度档) 缓存 AudioBuffer，连续扫弦零卡顿；上限 200 条防内存膨胀。
4. **面板交互三通道**：原生 click（鼠标）/ 悬停 0.7s dwell（摄像头）/ 捏合上升沿（摄像头）——同一 data-act 委托分发。
5. **鼓组=分区弦**：选鼓组乐器时弦上均分 5/4 个分区（底鼓/军鼓/踩镲/拍手/桶鼓 · 康加/金贝/邦戈/沙锤），扫过哪个区响哪个鼓。
6. **触屏手势拆分**（v1.1）：触屏没有 hover，"划弦演奏"与"拖拽画弦"物理上无法区分 → 画弦改为显式武装模式；徽章菜单只认"点按"（tap 判定：位移<12px 且 <400ms）；`touch-action:none` + 禁双击缩放 + 禁长按 callout/contextmenu，保证演奏不被浏览器手势劫持。

## 自动验收

`window.AIRSTRING` 调试 API（生产无副作用）：

```js
AIRSTRING.state          // {mode, strings, plucks, fps, camHands}
AIRSTRING.strings()      // 弦清单
AIRSTRING.instruments()  // 24 乐器 id 序列
AIRSTRING.pluck(inst, midi, vel)  // 直接触发一个音
AIRSTRING.energy()       // 输出总线 RMS 能量 0~1（验收合成真实出声）
AIRSTRING.demo()         // 三弦示例舞台
AIRSTRING.createString(x1,y1,x2,y2,opts)
AIRSTRING.loadTracker()  // 仅初始化手部模型（无摄像头也可验证 vendor 完整性）
```

## 已知边界 / 未实现（对标原版）

- 弯弦（bend & snap）手势：未实现（候选 v1.1）
- Air Pad 空间混音手势（拖动调暗度/回声）：未实现，改为设置面板滑条
- 节拍器 / 录制回放 / 多用户 Session：未实现
- Safari < 15 不支持 ES module 动态 import + AudioContext 新语法，未做兼容降级
