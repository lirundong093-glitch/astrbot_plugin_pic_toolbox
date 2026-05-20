"""摸头杀生成器：基于 B1gM8c/Petpet 算法，Python 重实现。

仅支持静态图片 + 头像，输出 112×112 的 5 帧 GIF。
"""

import os
from PIL import Image

_HAND_PATH = os.path.join(os.path.dirname(__file__), "petpet_hand.png")

# 5 帧的挤压偏移量 {dx, dy, dw, dh}
_FRAME_OFFSETS = [
    {"x": 0,  "y": 0,  "w": 0,  "h": 0},
    {"x": -4, "y": 12, "w": 4,  "h": -12},
    {"x": -12,"y": 18, "w": 12, "h": -18},
    {"x": -8, "y": 12, "w": 4,  "h": -12},
    {"x": -4, "y": 0,  "w": 0,  "h": 0},
]

OUT_SIZE = 112
SQUISH = 1.25
SCALE = 0.875
DELAY = 60  # ms
SPRITE_X = 14
SPRITE_Y = 20


def _load_hand():
    """加载手部精灵图（560×112，5 帧横排）"""
    hand = Image.open(_HAND_PATH).convert("RGBA")
    if hand.size != (560, 112):
        raise RuntimeError(f"精灵图尺寸异常: {hand.size}，期望 560×112")
    return hand


def _get_sprite_frame(off: dict):
    """计算某一帧的头像绘制区域"""
    dx = int(SPRITE_X + off["x"] * (SQUISH * 0.4))
    dy = int(SPRITE_Y + off["y"] * (SQUISH * 0.9))
    dw = int((OUT_SIZE + off["w"] * SQUISH) * SCALE)
    dh = int((OUT_SIZE + off["h"] * SQUISH) * SCALE)
    return dx, dy, dw, dh


def generate_petpet(input_path: str, output_path: str) -> str:
    """生成摸头杀 GIF。

    input_path  — 静态图片/头像路径
    output_path — 输出 GIF 路径
    """
    hand = _load_hand()
    avatar = Image.open(input_path).convert("RGBA")

    # 裁剪为正方形（取中心）
    w, h = avatar.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    avatar = avatar.crop((left, top, left + side, top + side))
    # 缩放到 112×112（适配手部精灵区域）
    avatar = avatar.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)

    frames = []
    for i, off in enumerate(_FRAME_OFFSETS):
        # 透明画布 112×112
        canvas = Image.new("RGBA", (OUT_SIZE, OUT_SIZE), (0, 0, 0, 0))

        # 绘制被挤压的头像
        dx, dy, dw, dh = _get_sprite_frame(off)
        squished = avatar.resize((dw, dh), Image.LANCZOS)
        canvas.paste(squished, (dx, dy), squished)

        # 绘制手（第 i 帧，每帧 112×112）
        hand_frame = hand.crop((i * OUT_SIZE, 0, (i + 1) * OUT_SIZE, OUT_SIZE))
        canvas.paste(hand_frame, (0, 0), hand_frame)

        frames.append(canvas)

    frames[0].save(
        output_path,
        "GIF",
        save_all=True,
        append_images=frames[1:],
        duration=[DELAY] * len(frames),
        loop=0,
        disposal=2,
        optimize=False,
    )
    return output_path
