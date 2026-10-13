# gif2avif — GIF 转 AVIF（支持动图）

纯 Python 小工具，把 `.gif` 转成 `.avif`。**动图会完整保留**（帧数、每帧时长、尺寸、透明通道），
不需要安装 FFmpeg。

## 依赖

* Python 3.9+
* Pillow **>= 11.3**（该版本的 wheel 内置 libavif 编码器，原生支持 AVIF 读写）

```bash
pip install -U "pillow>=11.3"
```

检查是否可用：

```bash
python -c "from PIL import features;print(features.check('avif'))"   # 需要输出 True
```

## 快速使用

```bash
python gif2avif.py demo.gif                     # 生成 demo.avif（与原文件同目录）
python gif2avif.py demo.gif -o out.avif         # 指定输出文件
python gif2avif.py ./gifs -o ./out -r           # 批量转换目录（含子目录）
python gif2avif.py a.gif b.gif -o ./out --force # 多个文件，覆盖已存在的输出
```

Windows 上也可以直接双击/命令行使用 `gif2avif.cmd`（会自动在 PATH 与常见 conda 环境里
挑选一个带 Pillow 的解释器，也可用 `set GIF2AVIF_PYTHON=...` 指定）：

```bat
gif2avif.cmd demo.gif
```

> 小提示：如果在**另一个 .bat/.cmd 脚本里**调用，按 cmd 的转义规则 `%` 要写成 `%%%%`，
> 例如 `--resize 50%%%%`；直接在命令行窗口输入时写 `--resize 50%` 即可。

## 常用参数

| 参数 | 说明 |
| --- | --- |
| `-o, --output` | 输出文件（单个输入）或输出目录（多个输入） |
| `-q, --quality` | 画质 0-100，默认 **80** |
| `-s, --speed` | 编码速度 0-10，越大越快但文件越大，默认 **6** |
| `--subsampling` | 色度采样 `4:4:4`（默认，图形/文字更锐利）/ `4:2:2` / `4:2:0`（更小） |
| `--resize WxH` | 缩放：`640x480`、`640x`、`x480`、`50%` |
| `--alpha auto\|keep\|drop` | 透明通道处理，默认 `auto`（有透明才保留） |
| `--default-duration MS` | GIF 中时长为 0 的帧按多少毫秒算，默认 100 |
| `--threads N` | 编码线程数，0=自动 |
| `-r, --recursive` | 目录输入时递归子目录（保留相对目录结构） |
| `-f, --force` / `--skip-existing` | 覆盖 / 跳过已存在的输出 |
| `--delete-source` | 转换成功后**删除源 GIF**（默认保留，详见下方安全说明） |
| `-n, --dry-run` | 只打印将要做什么 |
| `-v, --verbose` / `--quiet` | 更多细节 / 只输出错误 |

## 输出特点

* **单帧 GIF** → 普通静态 AVIF（`ftyp` 品牌 `avif`），兼容性最好；
* **多帧 GIF** → 动图 AVIF（`ftyp` 品牌 `avis`，视频轨道 + 可选的 alpha 辅助轨道）；
* 每帧时长按毫秒原样写入容器的时序表（`stts`），可在播放器里逐帧还原；
* 源图不含透明时自动按 RGB 编码，不写多余的 alpha 轨道；
* 写入采用「先写 `.part` 临时文件再改名」，中途失败不会留下损坏文件。

## `--delete-source` 安全说明

转换完成后自动删除源 GIF，适合「批量转换 + 清理」场景：

```bash
python gif2avif.py ./gifs -o ./out -r --delete-source
```

删除时机经过多重保护，**只有真的转换成功才会删**：

1. 输出文件先写成 `.part`，成功后才改名；改名前还会校验非空，编码失败不会留下半成品，也不会删源；
2. 转换抛异常、输出已存在被跳过、`--dry-run` 试运行 —— 上述情况源文件一律保留；
3. 删除前再确认「源文件路径 ≠ 输出文件路径」，删除失败只告警，不影响已生成的 AVIF；
4. 建议先用 `-n/--dry-run --delete-source` 看一遍将要发生什么，或先不带该参数转换一次确认效果。

## 已知限制

1. **循环次数**：Pillow 没有开放 AVIF 的循环次数参数，输出的动图使用 libavif 默认值（无限循环），
   GIF 的有限循环次数（如"播 3 次"）无法保留。
2. **解码器要求**：动图 AVIF 需要较新的解码器 —— Chrome 85+、Firefox 93+、Safari 16.4+、
   Windows 11 照片（带 AV1 扩展）等；老软件或部分图片查看器可能只认静态 AVIF。
   若担心兼容性，可对单帧图使用 `--subsampling 4:2:0`。
3. **内存**：所有帧需同时载入内存（Pillow 的保存接口要求），
   超大动图（如 500 帧 × 1000×1000）约需 2 GB 内存，工具会提前提示，可用 `--resize` 缩小。
4. 有损编码：`-q 100` 接近无损但（受 RGB↔YUV 转换影响）不保证 bit 级一致。

## 实测效果（本机测试）

| 源 GIF | 输出 AVIF | 结果 |
| --- | --- | --- |
| 402 KB，18 帧 512×512 | 296 KB | −26%，时长 30ms/帧 完全一致 |
| 318 KB，静态 640×480 | 74 KB | −77% |
| 1431 KB，499 帧 1012×1012 | 649 KB | −55%，17 秒，峰值内存 2.3 GB |

解码回读与源图逐帧比对，每通道平均绝对误差 < 1/255。
