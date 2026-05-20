"""GIF 速度调控：0.3x ~ 5.0x 变速"""

from PIL import Image
from .gif_utils import unfold_frames, save_kwargs_for


def parse_speed(s: str) -> float:
    try:
        v = round(float(s), 1)
    except (ValueError, TypeError):
        raise ValueError(f"无效的速度值: {s}")
    if v < 0.3 or v > 5.0:
        raise ValueError(f"速度范围 0.3 ~ 5.0，收到: {v}")
    return v


def adjust_gif_speed(input_path: str, output_path: str, speed: float) -> str:
    gif = Image.open(input_path)
    frames, durations = unfold_frames(gif)
    new_durs = [max(10, min(65535, int(d / speed))) for d in durations]

    kwargs = save_kwargs_for(gif, new_durs)
    kwargs.update(save_all=True, append_images=frames[1:] if len(frames) > 1 else [])
    frames[0].save(output_path, "GIF", **kwargs)
    return output_path
