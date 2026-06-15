"""GIF 通用工具：帧展开与类型判断，供 flip / invert / gif_speed / liquid_gif 共用"""

from PIL import Image, ImageSequence
import numpy as np
import struct


def is_gif(path: str) -> bool:
    try:
        with Image.open(path) as im:
            return getattr(im, "is_animated", False)
    except Exception:
        return path.lower().endswith(".gif")


def _get_background_rgba(gif: Image.Image):
    """获取 disposal=2 时的背景色。

    关键规则：若 GIF 定义了 transparency 索引（即存在透明色），
    则始终用全透明 (0,0,0,0) 作为背景——否则 disposal=2 会将透明
    区域恢复为 opaque 背景色，导致后续帧失去透明通道。
    仅当 GIF 无 transparency 时，才使用 background 索引对应的实际颜色。
    """
    trans_index = gif.info.get("transparency")
    if trans_index is not None:
        # GIF 有透明色 → 背景必须透明
        return (0, 0, 0, 0)
    palette = gif.getpalette()
    bg_index = gif.info.get("background")
    if bg_index is None:
        return (0, 0, 0, 0)
    if palette:
        base = bg_index * 3
        if base + 2 < len(palette):
            return (palette[base], palette[base + 1], palette[base + 2], 255)
    return (0, 0, 0, 0)


def unfold_frames(gif: Image.Image):
    """展开 GIF 增量帧为完整帧列表。

    逐帧复合到累积画布，尽量尊重 disposal=0/1/2/3。
    返回 (frames: list[Image], durations: list[int])，其中 frames 内全为独立 RGBA 完整帧。
    """
    frames, durations = [], []
    canvas_size = gif.size
    bg = Image.new("RGBA", canvas_size, _get_background_rgba(gif))

    composited = None
    previous_composited = None

    for frame in ImageSequence.Iterator(gif):
        disposal = getattr(frame, "disposal_method", None)
        if disposal is None:
            disposal = frame.info.get("disposal", 0)

        frame_rgba = frame.convert("RGBA")

        if composited is None:
            composited = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        else:
            if disposal == 2:
                composited = bg.copy()
            elif disposal == 3 and previous_composited is not None:
                composited = previous_composited.copy()
            else:
                composited = composited.copy()

        previous_composited = composited.copy()
        composited.alpha_composite(frame_rgba)

        frames.append(composited.copy())
        durations.append(frame.info.get("duration", gif.info.get("duration", 100)))

    return frames, durations


def save_kwargs_for(gif: Image.Image, durations: list) -> dict:
    """构建 GIF 保存参数，保留原图 loop。

    注意：不传递原 GIF 的 transparency 索引，因为帧经 RGBA 处理后
    会生成新调色板，旧索引不匹配。
    """
    return {
        "duration": durations,
        "loop": gif.info.get("loop", 0),
        "disposal": 2,
        "optimize": False,
    }


# ── LZW 编码器（GIF 格式） ──────────────────────

def _lzw_encode(data: bytes, min_code_size: int = 8) -> bytes:
    """GIF LZW 压缩。"""
    clear_code = 1 << min_code_size
    eoi_code = clear_code + 1
    next_code = eoi_code + 1
    code_size = min_code_size + 1
    max_code = 1 << code_size

    table = {}
    buf = _BitBuffer()
    buf.write(clear_code, code_size)

    prefix = data[0]
    for byte in data[1:]:
        key = (prefix << 8) | byte
        if key in table:
            prefix = table[key]
        else:
            buf.write(prefix, code_size)
            if next_code < 4096:
                table[key] = next_code
                next_code += 1
                if next_code > max_code and code_size < 12:
                    code_size += 1
                    max_code = 1 << code_size
            prefix = byte

    buf.write(prefix, code_size)
    buf.write(eoi_code, code_size)
    return buf.to_bytes()


class _BitBuffer:
    __slots__ = ('_data', '_bits', '_bit_count')

    def __init__(self):
        self._data = bytearray()
        self._bits = 0
        self._bit_count = 0

    def write(self, value: int, num_bits: int):
        self._bits |= (value & ((1 << num_bits) - 1)) << self._bit_count
        self._bit_count += num_bits
        while self._bit_count >= 8:
            self._data.append(self._bits & 0xFF)
            self._bits >>= 8
            self._bit_count -= 8

    def to_bytes(self) -> bytes:
        if self._bit_count:
            self._data.append(self._bits & 0xFF)
        return bytes(self._data)


# ── GIF 二进制写入 ─────────────────────────────

def _write_gif_sub_blocks(f, data: bytes):
    """写入 GIF sub-block 格式的数据。"""
    for i in range(0, len(data), 255):
        block = data[i:i + 255]
        f.write(struct.pack("<B", len(block)))
        f.write(block)
    f.write(b"\x00")  # 终止符


def save_rgba_gif(frames: list, durations: list, output_path: str,
                  loop: int = 0, disposal: int = 2,
                  source_palette=None, source_trans_idx=None):
    """保存 RGBA 帧列表为 GIF，正确保持透明背景。

    手工写入 GIF 二进制，确保：
    1. 所有帧共享同一个全局调色板（0 个局部调色板）
    2. 透明索引统一（所有帧同一个 transparent index）

    当提供 source_palette 时（原 GIF 的 getpalette() 结果），
    直接复用原调色板——避免重新量化导致的颜色偏移。
    适用于调速/翻转/对称等不改变像素颜色的操作。
    当未提供时（如反色操作），自动从第一帧量化生成新调色板。

    Args:
        frames: RGBA 帧列表
        durations: 每帧持续时间 (ms)
        output_path: 输出路径
        loop: 循环次数 (0=无限)
        disposal: 处置方式 (默认 2=恢复背景)
        source_palette: 可选，原 GIF 调色板 (768 bytes)
        source_trans_idx: 可选，原 GIF 透明索引
    """
    if not frames:
        return

    first_rgba = frames[0].convert("RGBA")
    has_alpha = any(
        (np.array(f.convert("RGBA").split()[-1], dtype=np.uint8) < 128).any()
        for f in frames
    )

    w, h = first_rgba.size

    # ── 1. 决定调色板 ──────────────────────
    if source_palette is not None:
        # 复用原调色板：无颜色偏移
        palette = list(source_palette)[:768]
        if len(palette) < 768:
            palette.extend([0] * (768 - len(palette)))
        trans_idx = source_trans_idx
        if trans_idx is None and has_alpha:
            # 原图无透明色但帧有透明像素 → 无可用透明索引，回退重量化
            first_p = first_rgba.quantize(colors=255, method=Image.Quantize.FASTOCTREE)
            palette = list(first_p.getpalette())[:768]
            trans_idx = first_p.info.get("transparency") or 0
            if len(palette) < 768:
                palette.extend([0] * (768 - len(palette)))
            template_p = first_p
        else:
            # 构建模板 P 图（仅用于提供给 quantize 的 palette 参考）
            template_p = Image.new("P", (1, 1))
            template_p.putpalette(palette)
    else:
        # 重新量化（反色等改变颜色的操作）
        first_p = first_rgba.quantize(colors=255, method=Image.Quantize.FASTOCTREE)
        palette = list(first_p.getpalette())[:768]
        trans_idx = first_p.info.get("transparency")
        if trans_idx is None:
            trans_idx = 0
        if len(palette) < 768:
            palette.extend([0] * (768 - len(palette)))
        template_p = first_p

    # ── 2. 将所有帧 remap 到同一调色板 ──────
    p_frames = []

    for f in frames:
        rgba = f.convert("RGBA") if f.mode != "RGBA" else f
        rgb = rgba.convert("RGB")
        quantized = rgb.quantize(palette=template_p)
        quant_arr = np.array(quantized, dtype=np.uint8)

        if trans_idx is not None and has_alpha:
            alpha = rgba.split()[-1]
            alpha_arr = np.array(alpha, dtype=np.uint8)
            quant_arr[alpha_arr < 128] = trans_idx
        p_frames.append(quant_arr)

    # ── 3. 写入 GIF 文件 ───────────────────
    with open(output_path, "wb") as f:
        # Header
        f.write(b"GIF89a")

        # Logical Screen Descriptor
        packed = 0xF7  # GCT present, 256 colors
        f.write(struct.pack("<HHBBB", w, h, packed, 0, 0))

        # Global Color Table
        f.write(bytes(palette[:768]))

        # Netscape Extension (loop)
        f.write(b"\x21\xFF\x0BNETSCAPE2.0\x03\x01")
        f.write(struct.pack("<H", loop & 0xFFFF))
        f.write(b"\x00")

        # 逐帧写入
        for i, pframe in enumerate(p_frames):
            dur_ms = durations[i] if i < len(durations) else 100
            dur_cs = max(1, min(65535, dur_ms // 10))

            # Graphic Control Extension
            disposal_bits = (disposal & 0x07) << 2
            has_trans = (trans_idx is not None and has_alpha)
            flags = disposal_bits | (0x01 if has_trans else 0x00)
            f.write(b"\x21\xF9\x04")
            t_idx = trans_idx if has_trans else 0
            f.write(struct.pack("<BBHB", flags, dur_cs, t_idx, 0))

            # Image Descriptor — 无局部调色板
            f.write(b"\x2C")
            f.write(struct.pack("<HHHH", 0, 0, w, h))
            f.write(b"\x00")

            # LZW 压缩
            min_code_size = 8
            compressed = _lzw_encode(pframe.tobytes(), min_code_size)
            f.write(struct.pack("<B", min_code_size))
            _write_gif_sub_blocks(f, compressed)

        # Trailer
        f.write(b"\x3B")
