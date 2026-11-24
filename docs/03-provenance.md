# 03 · 溯源与许可证

## 传播链

```
原作品: Hashem Al-Ghaili "Music Maker"（用 Claude 约 2 小时生成, 单 HTML 文件）
  └─ 演示视频经 RoundtableSpace 等账号传播
      └─ X 推文 @EmonData/status/2124626979743842530（2026-11, 中文转评）
          └─ 用户指令: "参照这个内容，克隆形成完整本地项目"
```

## 合规判定

| 项 | 判定 | 依据 |
|----|------|------|
| 原仓库 LICENSE | **不存在**（README.md + index.html 两文件，无任何许可证文件） | GitHub 默认版权保留（All Rights Reserved） |
| 处置 | **净室实现**：只对齐概念/交互/乐器清单等不受版权保护的思想（idea），应用代码 100% 重写 | 版权保护表达（expression）而非思想；本仓库 `index.html` 为独立编写 |
| 参考副本 | `_ref_music-maker` 仅用于功能面调研，已从项目目录删除，不分发 | 私下查看合法，不进入交付树 |
| MediaPipe tasks-vision 0.10.14 | Apache-2.0，本地 vendor 分发合法 | `vendor/mediapipe/LICENSE.tasks-vision`（完整 Apache-2.0 原文随附） |
| hand_landmarker float16 模型 | Apache-2.0（Google MediaPipe model card） | 同上 |

## 与原版的功能对照

| 维度 | 原版 | 本项目 |
|------|------|--------|
| 乐器 | 24 | 24（同一清单：guitar/egtr/harp/oud/qanun/sitar/piano/epiano/organ/marimba/kalimba/steelpan/violin/cello/strings/flute/trumpet/voices/bells/synth/bass/sub/drums/handdrums） |
| 音阶 | 7（major/minor/penta×2/blues/dorian/hijaz） | 同 7 种 |
| 造弦手势 | 双手捏合拉开松手 | 同 |
| 演奏 | 指尖扫弦拨奏 | 同（速度→力度） |
| 徽章 | 弦中点换乐器/音阶/调性/八度/和弦/删除 | 同 |
| 端点 | 拖动缩放，缩短删除 | 同 |
| 弯弦 bend & snap | 有 | **未实现**（v1.1 候选） |
| Air Pad 混音手势 | 有 | 改为设置面板滑条 |
| 指针 | 琥珀环收缩 | 同 |
| 无摄像头降级 | "Play with the mouse instead" | 同（鼠标/触摸，Pointer Events） |
| 运行依赖 | jsdelivr CDN（在线才能用） | **全离线** vendor（改进） |
| 设置 | 灵敏度等 | + 音量/回声/混响/灵敏度/视频开关，localStorage 持久化 |
| 自动验收 | 无 | window.AIRSTRING 调试 API |

## 后续若要公开发布

- 本仓库代码可自主决定许可证（净室 + Apache-2.0 依赖兼容 MIT/Apache-2.0 发布）
- 发布前措辞审查走既定红线流程；对外说明中注明 "inspired by Music Maker by Hashem Al-Ghaili"（致敬非义务，但推荐）
