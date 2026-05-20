"""GIF 通用工具：帧展开与类型判断，供 flip / invert / gif_speed / liquid_gif 共用"""

from PIL import Image, ImageSequence


def is_gif(path: str) -> bool:
    try:
        with Image.open(path) as im:
            return getattr(im, "is_animated", False)
    except Exception:
        return path.lower().endswith(".gif")


def _get_background_rgba(gif: Image.Image):
    palette = gif.getpalette()
    bg_index = gif.info.get("background")
    trans_index = gif.info.get("transparency")
    if bg_index is None or bg_index == trans_index:
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
    """构建 GIF 保存参数，保留原图 transparency / loop"""
    kwargs = {
        "duration": durations,
        "loop": gif.info.get("loop", 0),
        "disposal": 2,
        "optimize": False,
    }
    if "transparency" in gif.info:
        kwargs["transparency"] = gif.info["transparency"]
    return kwargs
