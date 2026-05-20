"""GIF 通用工具：帧展开与类型判断，供 flip / invert / gif_speed / liquid_gif 共用"""

from PIL import Image, ImageSequence


def is_gif(path: str) -> bool:
    try:
        with Image.open(path) as im:
            return getattr(im, "is_animated", False)
    except Exception:
        return path.lower().endswith(".gif")


def unfold_frames(gif: Image.Image):
    """展开 GIF 增量帧为完整帧列表。

    逐帧 composite 到 prev 累积画布上，尊重 disposal。
    返回 (frames: list[Image], durations: list[int])。
    """
    frames, durations = [], []
    canvas_size = gif.size
    prev = None
    bg = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    for frame in ImageSequence.Iterator(gif):
        f = frame.convert("RGBA")
        if prev is None:
            prev = f.copy()
        else:
            prev = prev.copy()
            prev.paste(f, (0, 0), f)

        frames.append(prev)
        durations.append(frame.info.get("duration", 100))

        if frame.info.get("disposal", 0) == 2:
            prev = bg.copy()

    return frames, durations


def save_kwargs_for(gif: Image.Image, durations: list) -> dict:
    """构建 GIF 保存参数，保留原图 transparency / loop"""
    kwargs = {
        "duration": durations,
        "loop": gif.info.get("loop", 0),
        "disposal": 2,
    }
    if "transparency" in gif.info:
        kwargs["transparency"] = gif.info["transparency"]
    return kwargs
