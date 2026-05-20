"""反色模块：静态图/GIF 反色处理"""

from PIL import Image, ImageOps
from .gif_utils import is_gif, unfold_frames, save_kwargs_for


def invert_image(input_path: str, output_path: str) -> str:
    gif = Image.open(input_path)

    if not is_gif(input_path):
        img = gif.convert("RGBA")
        r, g, b, a = img.split()
        ri, gi, bi = ImageOps.invert(Image.merge("RGB", (r, g, b))).split()
        Image.merge("RGBA", (ri, gi, bi, a)).save(output_path, "PNG")
        return output_path

    frames, durations = unfold_frames(gif)
    inverted = []
    for f in frames:
        r, g, b, a = f.split()
        ri, gi, bi = ImageOps.invert(Image.merge("RGB", (r, g, b))).split()
        inverted.append(Image.merge("RGBA", (ri, gi, bi, a)))

    kwargs = save_kwargs_for(gif, durations)
    kwargs.update(save_all=True, append_images=inverted[1:] if len(inverted) > 1 else [])
    inverted[0].save(output_path, "GIF", **kwargs)
    return output_path
