#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gif2avif —— 把 GIF（含动图）转换成 AVIF。

特点
----
* 纯 Python，只依赖 Pillow（>= 11.3 自带 libavif 编码器），不需要 FFmpeg；
* 动图完整保留：帧数、每帧时长、画面尺寸；
* 透明背景保留：以 AVIF 的 alpha 辅助轨道写入；源图不透明时自动按 RGB 编码（体积更小）；
* 支持单文件 / 多文件 / 整个目录（可递归）批量转换；
* 支持缩放、质量、编码速度、色度采样等参数调优。

用法
----
    python gif2avif.py demo.gif                    # 生成 demo.avif
    python gif2avif.py demo.gif -o out.avif        # 指定输出文件
    python gif2avif.py demo.gif -q 90 -s 4         # 更高质量（更慢）
    python gif2avif.py ./gifs -o ./out -r          # 批量转换目录里的 gif
    python gif2avif.py a.gif b.gif -o ./out --force
    python gif2avif.py ./gifs -o ./out -r --delete-source   # 转完删除源 GIF

注意
----
* AVIF 动图（ftyp 品牌 avis）由较新的解码器支持：Chrome 85+ / Firefox 93+ / Safari 16.4+ 等。
  静态 GIF 会输出普通静态 AVIF，兼容性更好。
* GIF 的有限循环次数无法保留（Pillow 未开放该参数），输出的动图会无限循环。
* --delete-source 会删除源文件：只在「输出文件已成功写出且非空」之后才执行，
  转换失败、跳过、试运行（--dry-run）都不会删除。
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# ---------------------------------------------------------------- 依赖检查

try:
    from PIL import Image, features as pil_features
except ImportError:  # pragma: no cover
    sys.exit("缺少依赖 Pillow，请先安装：pip install -U \"pillow>=11.3\"")

DEFAULT_QUALITY = 80          # libavif quality: 0(最差) - 100(最好)
DEFAULT_SPEED = 6             # libavif speed:   0(最慢最小) - 10(最快最大)
DEFAULT_SUBSAMPLING = "4:4:4"  # GIF 多为图形/文字，4:4:4 保留锐利边缘，体积仅略增
DEFAULT_FRAME_MS = 100        # GIF 中时长为 0 的帧按 100 ms 计（与浏览器行为一致）
MIN_PILLOW = (11, 3)

RESAMPLING = getattr(Image, "Resampling", Image).LANCZOS  # Pillow 9.1+ / 旧版兼容


def avif_capability() -> Tuple[bool, bool, Optional[str]]:
    """检测 AVIF 写出能力。

    返回 (能否写 AVIF, 能否写动图 AVIF, 提示信息)。
    """
    Image.init()  # 强制加载插件，便于发现第三方 AVIF 插件
    if pil_features.check("avif"):
        return True, True, None
    if "AVIF" in Image.SAVE:  # 例如 pillow-avif-plugin
        return True, False, "检测到第三方 AVIF 插件：仅支持静态图，动图会退化为单帧"
    return False, False, (
        "当前 Pillow 不支持 AVIF 写出。请升级：pip install -U \"pillow>=11.3\""
        f"（Pillow 版本 {Image.__version__}，需要 >= {'.'.join(map(str, MIN_PILLOW))}）"
    )


# ---------------------------------------------------------------- 参数解析

def parse_resize(spec: str, size: Tuple[int, int]) -> Tuple[int, int]:
    """把 --resize 的写法解析成像素尺寸。

    支持 "640x480"、"640x"、"x480"、"50%"（等比缩放）。
    """
    src_w, src_h = size
    spec = spec.strip().lower()

    if spec.endswith("%"):
        try:
            ratio = float(spec[:-1]) / 100.0
        except ValueError:
            raise argparse.ArgumentTypeError(f"无法识别的缩放比例: {spec}")
        if ratio <= 0:
            raise argparse.ArgumentTypeError("缩放比例必须大于 0")
        return max(1, round(src_w * ratio)), max(1, round(src_h * ratio))

    if "x" not in spec:
        raise argparse.ArgumentTypeError(f"无法识别的尺寸写法: {spec}（示例 640x480 / 640x / 50%）")

    left, _, right = spec.partition("x")
    try:
        w = int(left) if left.strip() else 0
        h = int(right) if right.strip() else 0
    except ValueError:
        raise argparse.ArgumentTypeError(f"无法识别的尺寸写法: {spec}")

    if w <= 0 and h <= 0:
        raise argparse.ArgumentTypeError(f"无法识别的尺寸写法: {spec}")

    if w > 0 and h > 0:
        return w, h
    if w > 0:                                   # 只给宽度，按比例算高度
        return w, max(1, round(src_h * w / src_w))
    return max(1, round(src_w * h / src_h)), h  # 只给高度


# ---------------------------------------------------------------- GIF 读取

def load_gif(path: Path, default_ms: int, keep_alpha: str):
    """读取 GIF 的全部帧（全部解码进内存，动图较大时请注意内存占用）。

    返回 (帧列表[RGB/RGBA], 每帧时长[ms], 源循环次数, 是否含透明, 原始尺寸)。
    """
    frames: List[Image.Image] = []
    durations: List[int] = []
    has_alpha = keep_alpha == "keep"

    with Image.open(path) as im:
        n_frames = getattr(im, "n_frames", 1)
        loop = im.info.get("loop")
        src_size = im.size

        for index in range(n_frames):
            im.seek(index)                       # 必须顺序 seek，Pillow 才会正确合成 dispose 帧
            duration = int(im.info.get("duration", 0) or 0)
            durations.append(duration if duration > 0 else default_ms)

            # 声明了透明索引的帧才需要 alpha 通道；其余帧直接按 RGB 保存（省内存、文件更小）
            if keep_alpha == "drop" or not (keep_alpha == "keep"
                                            or im.info.get("transparency") is not None):
                frames.append(im.convert("RGB"))
                continue

            frame = im.convert("RGBA")           # GIF 的调色板/局部帧/透明在这里被正确合成
            if frame.getchannel("A").getextrema()[0] < 255:
                has_alpha = True
            frames.append(frame)

    if not frames:
        raise ValueError("GIF 中没有可用的帧")

    # 统一各帧模式：AVIF 编码器要求整段动画的通道数一致
    target_mode = "RGBA" if has_alpha else "RGB"
    for i, frame in enumerate(frames):
        if frame.mode != target_mode:
            frames[i] = frame.convert(target_mode)

    return frames, durations, loop, has_alpha, src_size


def resize_frames(frames: Sequence[Image.Image], size: Tuple[int, int]) -> List[Image.Image]:
    if size == frames[0].size:
        return list(frames)
    return [f.resize(size, RESAMPLING) for f in frames]


# ---------------------------------------------------------------- 转换核心

def save_avif(frames: Sequence[Image.Image], durations: Sequence[int], out_path: Path,
              quality: int, speed: int, subsampling: str, threads: int,
              allow_animation: bool) -> None:
    """把帧序列写成 AVIF；多帧则写成动图 AVIF（avis）。"""
    kwargs = dict(format="AVIF", quality=quality, speed=speed, subsampling=subsampling)
    if threads > 0:
        kwargs["max_threads"] = threads

    multi = len(frames) > 1
    if multi and allow_animation:
        kwargs["save_all"] = True
        kwargs["append_images"] = list(frames[1:])
        kwargs["duration"] = list(durations)     # 逐帧时长（毫秒）

    tmp_path = out_path.with_name(out_path.name + ".part")
    try:
        frames[0].save(tmp_path, **kwargs)       # 先写临时文件，成功后再改名，避免半成品
        if tmp_path.stat().st_size <= 0:
            raise OSError("编码结果为空文件")
        tmp_path.replace(out_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


MEMORY_WARN_BYTES = 1024 ** 3               # 超过 1 GiB 时提醒一次


def probe_gif(path: Path) -> Tuple[int, Tuple[int, int], int]:
    """读出帧数与尺寸，并估算全部帧解码到内存所需字节数（按 RGBA 4 字节/像素）。"""
    with Image.open(path) as im:
        n_frames, size = getattr(im, "n_frames", 1), im.size
    return n_frames, size, n_frames * size[0] * size[1] * 4


def convert_one(src: Path, dst: Path, args, can_animate: bool) -> Tuple[bool, str]:
    """转换单个文件，返回 (是否成功, 说明文字)。"""
    t0 = time.time()

    n_frames, (w, h), estimate = probe_gif(src)
    if estimate > MEMORY_WARN_BYTES and not args.quiet:
        print(f"提示: {src.name} 有 {n_frames} 帧 {w}x{h}，全部载入内存约需 "
              f"{estimate / 2 ** 30:.1f} GB；内存不足时可用 --resize 缩小",
              file=sys.stderr)

    frames, durations, loop, has_alpha, src_size = load_gif(src, args.default_duration, args.alpha)

    if args.resize:
        size = parse_resize(args.resize, src_size)
        frames = resize_frames(frames, size)
    else:
        size = src_size

    note = ""
    if len(frames) > 1 and not can_animate:
        note = "（当前后端不支持动图，只写出第 1 帧）"
        frames, durations = frames[:1], durations[:1]

    save_avif(frames, durations, dst, args.quality, args.speed,
              args.subsampling, args.threads, allow_animation=can_animate)

    src_kb = src.stat().st_size / 1024
    dst_kb = dst.stat().st_size / 1024
    ratio = (dst_kb / src_kb - 1) * 100 if src_kb else 0
    elapsed = time.time() - t0

    kind = "动图" if len(frames) > 1 else "静态"
    alpha = "含透明" if has_alpha else "不透明"
    detail = (f"{kind} {len(frames)} 帧 {size[0]}x{size[1]} {alpha} "
              f"{src_kb:,.1f} KB -> {dst_kb:,.1f} KB ({ratio:+.0f}%) {elapsed:.1f}s")
    if args.verbose and loop is not None:
        detail += f" [源循环={loop}]"
    return True, detail + note


# ---------------------------------------------------------------- 输入/输出

def collect_inputs(paths: Sequence[str], recursive: bool) -> List[Tuple[Path, Optional[Path]]]:
    """收集输入文件，目录输入会记录其根目录用于保留相对结构。

    返回 [(gif 路径, 所在输入目录 或 None)]。
    """
    items: List[Tuple[Path, Optional[Path]]] = []
    seen = set()
    for raw in paths:
        p = Path(raw).expanduser()
        if p.is_dir():
            pattern = "**/*.gif" if recursive else "*.gif"
            found = sorted(q for q in p.glob(pattern) if q.is_file())
            if not found:
                print(f"警告: 目录中没有 gif 文件: {p}", file=sys.stderr)
            items.extend((q, p) for q in found)
        elif p.is_file():
            items.append((p, None))
        else:
            print(f"警告: 找不到输入: {p}", file=sys.stderr)

    out: List[Tuple[Path, Optional[Path]]] = []
    for src, base in items:
        key = str(src.resolve()).lower()
        if key not in seen:
            seen.add(key)
            out.append((src, base))
    return out


def delete_source(src: Path, dst: Path) -> bool:
    """删除已转换成功的源文件；任何异常都只警告、不影响已生成的输出。

    只在调用方确认「输出文件已成功生成」之后才会走到这里。
    """
    try:
        if src.resolve() == dst.resolve():       # 保险起见，绝不动输出文件本身
            print(f"警告: 源文件与输出文件是同一个文件，未删除: {short(src)}", file=sys.stderr)
            return False
        src.unlink()
        return True
    except OSError as exc:
        print(f"警告: 转换成功，但删除源文件失败: {short(src)}（{exc}）", file=sys.stderr)
        return False


def is_file_target(output: Optional[Path], many: bool) -> bool:
    """判断 -o 是否被写成了一个明确的输出文件名（而不是目录）。"""
    if output is None or many:
        return False
    return output.suffix.lower() in (".avif", ".avifs") and not output.is_dir()


def target_path(src: Path, output: Optional[Path], file_target: bool,
                base: Optional[Path]) -> Path:
    """算出输出路径：默认与原文件同目录同名 .avif；给了目录则放进去（保留相对结构）。"""
    if output is None:
        return src.with_name(src.with_suffix(".avif").name)
    if file_target:
        return output
    if base is not None:                       # 目录输入：保留子目录层级
        return output / src.relative_to(base).with_suffix(".avif")
    return output / src.with_suffix(".avif").name


def unique_path(path: Path, used: dict) -> Path:
    """同一次运行里输出路径重复时自动加序号，避免互相覆盖。"""
    if path not in used:
        return path
    stem, suffix, i = path.stem, path.suffix, 2
    while True:
        candidate = path.with_name(f"{stem} ({i}){suffix}")
        if candidate not in used:
            return candidate
        i += 1


def short(path: Path) -> str:
    """尽量显示相对当前目录的短路径，方便辨认。"""
    try:
        return os.path.relpath(path)
    except ValueError:                          # 跨盘符时退化为绝对路径
        return str(path)


def human_list(paths: Sequence[Path], limit: int = 3) -> str:
    names = [short(p) for p in paths[:limit]]
    if len(paths) > limit:
        names.append(f"... 共 {len(paths)} 个")
    return "、".join(names)


# ---------------------------------------------------------------- 命令行入口

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gif2avif",
        description="把 GIF（含动图）转换为 AVIF。纯 Python 实现，只依赖 Pillow>=11.3。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
               "  python gif2avif.py demo.gif\n"
               "  python gif2avif.py demo.gif -o out.avif -q 90\n"
               "  python gif2avif.py ./gifs -o ./out -r --force\n",
    )
    parser.add_argument("inputs", nargs="+", help="GIF 文件，或包含 GIF 的目录")
    parser.add_argument("-o", "--output", type=Path,
                        help="输出文件（单个输入）或输出目录（多个输入）；默认与原文件同目录")
    parser.add_argument("-q", "--quality", type=int, default=DEFAULT_QUALITY,
                        help=f"画质 0-100，越大越好也越大，默认 {DEFAULT_QUALITY}")
    parser.add_argument("-s", "--speed", type=int, default=DEFAULT_SPEED,
                        help=f"编码速度 0-10，越大越快但文件越大，默认 {DEFAULT_SPEED}")
    parser.add_argument("--subsampling", choices=("4:4:4", "4:2:2", "4:2:0"),
                        default=DEFAULT_SUBSAMPLING,
                        help=f"色度采样，默认 {DEFAULT_SUBSAMPLING}（图形/文字更锐利；4:2:0 体积更小）")
    parser.add_argument("--resize", metavar="WxH",
                        help="缩放，例如 640x480 / 640x / x480 / 50%%")
    parser.add_argument("--alpha", choices=("auto", "keep", "drop"), default="auto",
                        help="透明通道处理：auto=有透明才保留（默认），keep=始终保留，drop=始终丢弃")
    parser.add_argument("--default-duration", type=int, default=DEFAULT_FRAME_MS, metavar="MS",
                        help=f"GIF 中时长为 0 的帧使用的毫秒数，默认 {DEFAULT_FRAME_MS}")
    parser.add_argument("--threads", type=int, default=0,
                        help="AVIF 编码线程数，0=自动（默认）")
    parser.add_argument("-r", "--recursive", action="store_true", help="目录输入时递归子目录")
    parser.add_argument("-f", "--force", action="store_true", help="覆盖已存在的输出文件")
    parser.add_argument("--skip-existing", action="store_true", help="跳过已存在的输出文件")
    parser.add_argument("--delete-source", action="store_true",
                        help="转换成功后删除源 GIF 文件（默认保留；仅在输出确实生成成功后才删）")
    parser.add_argument("-n", "--dry-run", action="store_true", help="只显示将要做什么，不写文件")
    parser.add_argument("-v", "--verbose", action="store_true", help="输出更多细节")
    parser.add_argument("--quiet", action="store_true", help="只输出错误")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    # Windows 控制台默认不是 UTF-8，避免中文乱码
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = build_parser()
    args = parser.parse_args(argv)

    def log(msg: str = "") -> None:
        if not args.quiet:
            print(msg)

    if not (0 <= args.quality <= 100):
        parser.error("--quality 必须在 0-100 之间")
    if not (0 <= args.speed <= 10):
        parser.error("--speed 必须在 0-10 之间")
    if args.force and args.skip_existing:
        parser.error("--force 与 --skip-existing 不能同时使用")
    if args.resize:
        try:
            parse_resize(args.resize, (100, 100))   # 提前校验写法，避免每帧才报错
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))

    can_write, can_animate, hint = avif_capability()
    if not can_write:
        print(f"错误: {hint}", file=sys.stderr)
        return 2
    if hint:
        print(f"提示: {hint}", file=sys.stderr)

    sources = collect_inputs(args.inputs, args.recursive)
    if not sources:
        print("错误: 没有找到任何可转换的 GIF 文件", file=sys.stderr)
        return 2

    many = len(sources) > 1
    file_target = is_file_target(args.output, many)
    if args.output is not None and not file_target and not args.dry_run:
        try:
            args.output.mkdir(parents=True, exist_ok=True)
        except OSError as exc:                  # 例如 -o 指向了一个已存在的普通文件
            print(f"错误: 无法创建输出目录 {args.output}（{exc}）", file=sys.stderr)
            return 2

    log(f"待转换 {len(sources)} 个文件: {human_list([s for s, _ in sources])}")
    log()

    ok = skipped = failed = deleted = 0
    used: dict = {}
    for src, base in sources:
        dst = target_path(src, args.output, file_target, base)
        if dst in used:                       # 不同目录下的同名文件，自动加序号
            renamed = unique_path(dst, used)
            print(f"警告: 输出重名，{src.name} 改写为 {renamed.name}", file=sys.stderr)
            dst = renamed
        used[dst] = src

        if args.dry_run:
            suffix = "，并删除源文件" if args.delete_source else ""
            log(f"[试运行] {short(src)}  ->  {short(dst)}{suffix}")
            continue

        if dst.exists() and not args.force:
            if args.skip_existing:
                skipped += 1
                log(f"跳过（已存在）: {short(dst)}")
                continue
            print(f"错误: 输出已存在，加 --force 覆盖或 --skip-existing 跳过: {short(dst)}",
                  file=sys.stderr)
            failed += 1
            continue

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            success, detail = convert_one(src, dst, args, can_animate)
        except Exception as exc:  # 单个文件失败不影响批量
            print(f"失败: {short(src)} -> {exc}", file=sys.stderr)
            failed += 1
            continue

        if success:
            ok += 1
            if args.delete_source and delete_source(src, dst):   # 输出已确认生成，才删源文件
                deleted += 1
                detail += "，已删除源文件"
            log(f"完成: {short(src)} -> {short(dst)}\n      {detail}")

    if not args.dry_run:
        log()
        summary = f"合计: 成功 {ok}"
        if args.delete_source:
            summary += f"（已删除源文件 {deleted} 个）"
        log(summary + f"，跳过 {skipped}，失败 {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
