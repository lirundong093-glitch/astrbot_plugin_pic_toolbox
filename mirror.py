"""镜像对称模块：左/右/上/下半边对称，支持静态图和 GIF"""

from PIL import Image
from .gif_utils import is_gif, unfold_frames, save_kwargs_for


def _mirror_static(img: Image.Image, keep: str) -> Image.Image:
    """对单帧执行半边对称"""
    w, h = img.size
    if keep == "left":
        half = img.crop((0, 0, w // 2, h))
        flipped = half.transpose(Image.FLIP_LEFT_RIGHT)
        result = Image.new("RGBA", (w, h))
        result.paste(half, (0, 0))
        result.paste(flipped, (w // 2, 0))
    elif keep == "right":
        half = img.crop((w // 2, 0, w, h))
        flipped = half.transpose(Image.FLIP_LEFT_RIGHT)
        result = Image.new("RGBA", (w, h))
        result.paste(flipped, (0, 0))
        result.paste(half, (w // 2, 0))
    elif keep == "top":
        half = img.crop((0, 0, w, h // 2))
        flipped = half.transpose(Image.FLIP_TOP_BOTTOM)
        result = Image.new("RGBA", (w, h))
        result.paste(half, (0, 0))
        result.paste(flipped, (0, h // 2))
    else:  # bottom
        half = img.crop((0, h // 2, w, h))
        flipped = half.transpose(Image.FLIP_TOP_BOTTOM)
        result = Image.new("RGBA", (w, h))
        result.paste(flipped, (0, 0))
        result.paste(half, (0, h // 2))
    return result


def _mirror_gif(input_path: str, output_path: str, keep: str) -> str:
    gif = Image.open(input_path)
    frames, durations = unfold_frames(gif)
    mirrored = [_mirror_static(f, keep) for f in frames]

    kwargs = save_kwargs_for(gif, durations)
    kwargs.update(save_all=True, append_images=mirrored[1:] if len(mirrored) > 1 else [])
    mirrored[0].save(output_path, "GIF", **kwargs)
    return output_path


def mirror_left(input_path: str, output_path: str) -> str:
    """左半边对称到右边"""
    if is_gif(input_path):
        return _mirror_gif(input_path, output_path, "left")
    img = Image.open(input_path).convert("RGBA")
    _mirror_static(img, "left").save(output_path, "PNG")
    return output_path


def mirror_right(input_path: str, output_path: str) -> str:
    """右半边对称到左边"""
    if is_gif(input_path):
        return _mirror_gif(input_path, output_path, "right")
    img = Image.open(input_path).convert("RGBA")
    _mirror_static(img, "right").save(output_path, "PNG")
    return output_path


def mirror_top(input_path: str, output_path: str) -> str:
    """上半边对称到下边"""
    if is_gif(input_path):
        return _mirror_gif(input_path, output_path, "top")
    img = Image.open(input_path).convert("RGBA")
    _mirror_static(img, "top").save(output_path, "PNG")
    return output_path


def mirror_bottom(input_path: str, output_path: str) -> str:
    """下半边对称到上边"""
    if is_gif(input_path):
        return _mirror_gif(input_path, output_path, "bottom")
    img = Image.open(input_path).convert("RGBA")
    _mirror_static(img, "bottom").save(output_path, "PNG")
    return output_path
