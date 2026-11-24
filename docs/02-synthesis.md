# 02 · 24 乐器合成配方

全部实时合成（AudioContext, 44.1/48kHz），无任何采样。主链：

```
voice ─┬─> masterGain ─> DynamicsCompressor(-14dB, 5:1) ─> Analyser ─> destination
       ├─> echoSend ─> Delay 290ms ─> LPF 3.2k ─> 反馈36% ─┐ （回声并行）
       └─> revSend ─> Convolver(生成式IR 2.2s, 指数衰减白噪声) （混响并行）
```

## 拨弦族（Karplus-Strong 物理建模）

预计算：延迟线长度 = sr/f，初始激励为亮度低通白噪声，循环 `y[n] = damp·½(x[n]+x[n+1])`，峰值归一后按力度缩放。

| 乐器 | bright | damp | dur | 特色 |
|------|--------|------|-----|------|
| Guitar | .55 | .9960 | 2.6s | — |
| E-Guitar | .82 | .9970 | 2.4s | +tanh(×4) 软削失真 + 3.4k 音色低通 |
| Harp | .74 | .9948 | 3.2s | — |
| Oud | .60 | .9940 | 1.9s | 短衰减（羊肠弦感） |
| Qanun | .70 | .9950 | 2.2s | — |
| Sitar | .86 | .9970 | 3.4s | buzz=0.3 随机抖动模拟 jawari 嗡鸣 |

## 键盘/色彩族（加法 + FM）

- **Piano**：6 分音 [1,2,3,4,5,6]，幅度 1/.5/.28/.16/.1/.06，非谐系数 B=4e-4，高次分音指数快衰减
- **E-Piano**：FM（载波 sine，调制比 1:1，指数 5→0.05 in 450ms）+ 14 倍频"叮"起音（120ms）
- **Organ**：拉杆组合 [.5,1,2,3,4,8] 持续正弦
- **Marimba**：分音 [1, 3.93, 9.2]（木琴非谐），0.9s
- **Kalimba**：[1, 2.4, 5.1]，1.1s
- **Steel Pan**：[1, 2.02, 3.05, 4.6]，1.6s
- **Bells**：[1, 2.76, 5.4, 8.9]（钟形非谐），2.8s
- **Synth**：saw+sub square → 低通 2400→500Hz 指数扫频，Q=7

## 持续族（运弓/吹奏/人声）

统一骨架：2-3 个失谐振荡器 → 低通 → AD-R 包络（attack 后保持 dur 再 release），颤音 LFO（0.25s 后渐入）。

| 乐器 | 波形 | 截止 | attack | dur | 特色 |
|------|------|------|--------|-----|------|
| Violin | saw×2 | 2.8k | .12 | 1.3 | vib 6Hz |
| Cello | saw×2 | 1.4k | .16 | 1.5 | vib 5Hz，暗 |
| Strings | saw×3(-7,0,+7¢) | 2.6k | .18 | 1.6 | 合奏 detune |
| Flute | sine+2.005次谐 | 5k | .08 | 1.2 | 带通气噪声（带通白噪声跟随包络） |
| Trumpet | square+saw | 2k→4.6k 扫 | .05 | 1.0 | 亮度包络 |
| Voices | saw×3 | — | .22 | 1.8 | 双共振峰 660/1080Hz（"ah"） |
| Organ | sine×6 | — | .015 | 0.8 | 加法拉杆 |

## 低音族

- **Bass**：saw → 低通 900→240Hz 扫频 + 正弦 sub(60%)，0.8s
- **808 Bass**：sine 音高 2.2f→f 指数滑落（70ms）+ tanh(2.4) 饱和，1.4s 长衰减

## 鼓组（纯合成）

| 鼓 | 配方 |
|----|------|
| Kick | sine 165→44Hz + 起音白噪低通 3k |
| Snare | 带通白噪 1.9k + 210→150Hz 音头 |
| Hat | 高通白噪 8.2k，55ms |
| Clap | 3 连带通噪声（间隔 11ms），1.5k |
| Tom | sine 230→120Hz |
| Conga | sine 310→265 + 高噪起音 |
| Djembe | sine 185→150 + 900Hz 带通鼓皮拍 |
| Bongo | sine 560→520，短 |
| Shaker | 高通白噪 5.8k |

## 调性系统

- `degreeMidi(scale, root, oct, deg)`：oct=2 时根音=C4(60)；乐器默认八度：bass/sub=1，cello=2，guitar 族/piano 族=3，violin/bells=4/5
- 音阶：major [0,2,4,5,7,9,11] / minor / pentamaj [0,2,4,7,9] / pentamin [0,3,5,7,10] / blues [0,3,5,6,7,10] / dorian / hijaz [0,1,4,5,7,8,10]
- 和弦模式：拨 1 音自动叠 deg+2 / deg+4（力度 .7/.55）
