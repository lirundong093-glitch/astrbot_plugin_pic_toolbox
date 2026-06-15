"""翻转模块：静态图/GIF 左右翻转、上下翻转"""

from PIL import Image
from .gif_utils import is_gif, unfold_frames, save_rgba_gif


def flip_horizontal(input_path: str, output_path: str) -> str:
    if is_gif(input_path):
        return _flip_gif(input_path, output_path, Image.FLIP_LEFT_RIGHT)
    img = Image.open(input_path).convert("RGBA")
    img.transpose(Image.FLIP_LEFT_RIGHT).save(output_path, "PNG")
    return output_path



def flip_vertical(input_path: str, output_path: str) -> str:
    if is_gif(input_path):
        return _flip_gif(input_path, output_path, Image.FLIP_TOP_BOTTOM)
    img = Image.open(input_path).convert("RGBA")
    img.transpose(Image.FLIP_TOP_BOTTOM).save(output_path, "PNG")
    return output_path



def _flip_gif(input_path: str, output_path: str, method) -> str:
    gif = Image.open(input_path)
    src_palette = gif.getpalette()
    src_trans = gif.info.get("transparency")
    frames, durations = unfold_frames(gif)
    flipped_frames = [frame.convert("RGBA").transpose(method) for frame in frames]

    save_rgba_gif(flipped_frames, durations, output_path, loop=gif.info.get("loop", 0),
                  source_palette=src_palette,
                  source_trans_idx=src_trans)
    return output_path
