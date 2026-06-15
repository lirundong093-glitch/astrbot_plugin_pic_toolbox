"""GIF 速度调控：0.3x ~ 5.0x 变速，支持 50 FPS 上限回退与均匀丢帧"""

from PIL import Image
from .gif_utils import unfold_frames, save_rgba_gif

_GIF_MIN_DURATION_MS = 20       # 业务上限：帧间隔不低于 20ms（→ 最高 50 FPS）
_GIF_MAX_FPS = 1000 // _GIF_MIN_DURATION_MS  # 50


def parse_speed(s: str) -> float:
    try:
        v = round(float(s), 1)
    except (ValueError, TypeError):
        raise ValueError(f"无效的速度值: {s}")
    if v < 0.3 or v > 5.0:
        raise ValueError(f"速度范围 0.3 ~ 5.0，收到: {v}")
    return v


def adjust_gif_speed(
    input_path: str,
    output_path: str,
    speed: float,
    allow_frame_drop: bool = False,
) -> tuple:
    """调速 GIF，返回 (output_path, actual_speed, warning_msg_or_None)。

    - speed: 目标倍率（0.3 ~ 5.0）
    - allow_frame_drop: 当倍率使帧率超过 50 FPS 时，是否允许通过均匀丢帧
      来实现目标倍率（默认 False 时自动回退到最高不超过 50 FPS 的倍率）。
    """
    gif = Image.open(input_path)
    src_palette = gif.getpalette()
    src_trans = gif.info.get("transparency")
    frames, durations = unfold_frames(gif)

    frame_count = len(frames)
    if frame_count == 0:
        frames[0].save(output_path, "GIF")
        return output_path, speed, None

    total_dur_ms = sum(durations)
    if total_dur_ms <= 0:
        total_dur_ms = frame_count * 100  # 假设默认 100ms/帧

    # 原始平均 FPS
    original_avg_fps = frame_count * 1000.0 / total_dur_ms
    # 调速后的目标 FPS
    target_fps = original_avg_fps * speed

    # ── 情况 1：目标 FPS 在 50 以内，直接调速 ──
    if target_fps <= _GIF_MAX_FPS:
        new_durs = [max(_GIF_MIN_DURATION_MS, min(65535, int(d / speed))) for d in durations]
        save_rgba_gif(frames, new_durs, output_path, loop=gif.info.get("loop", 0),
                      source_palette=src_palette,
                      source_trans_idx=src_trans)
        return output_path, speed, None

    # ── 情况 2：不允许丢帧 → 回退到不超过 50 FPS 的最高倍率 ──
    if not allow_frame_drop:
        max_multiplier = _GIF_MAX_FPS / original_avg_fps
        max_multiplier = round(max_multiplier * 10) / 10  # 保留 1 位小数
        if max_multiplier > 5.0:
            max_multiplier = 5.0
        if max_multiplier < 0.3:
            max_multiplier = 0.3

        actual_fps = original_avg_fps * max_multiplier if max_multiplier >= 0.3 else original_avg_fps * 0.3
        new_durs = [max(_GIF_MIN_DURATION_MS, min(65535, int(d / max_multiplier))) for d in durations]
        save_rgba_gif(frames, new_durs, output_path, loop=gif.info.get("loop", 0),
                      source_palette=src_palette,
                      source_trans_idx=src_trans)

        warning = (
            f"⚠️ GIF 调速提醒：原 GIF {original_avg_fps:.1f} FPS，"
            f"×{speed} 后帧率将达 {target_fps:.0f} FPS，"
            f"超出 50 FPS 上限。\n"
            f"已自动回退至 ×{max_multiplier}（≈ {actual_fps:.0f} FPS）。"
        )
        return output_path, max_multiplier, warning

    # ── 情况 3：允许丢帧 → 均匀丢弃帧以实现目标倍率 ──
    # 逻辑：计算目标总时长下最多可保留多少帧（≥20ms/帧），
    # 然后均匀丢弃。速度提升仅通过丢帧实现，不改变单帧间隔。
    import math
    target_total_ms = total_dur_ms / speed
    max_keepable = math.ceil(target_total_ms / _GIF_MIN_DURATION_MS)
    if max_keepable < 1:
        max_keepable = 1
    keep_every = math.ceil(frame_count / max_keepable)

    kept_frames = frames[::keep_every]
    kept_durations = durations[::keep_every]

    # 丢帧模式下不修改单帧间隔，仅通过丢帧实现加速
    new_durs = kept_durations
    save_rgba_gif(kept_frames, new_durs, output_path, loop=gif.info.get("loop", 0),
                  source_palette=src_palette,
                  source_trans_idx=src_trans)

    # 计算实际达到的倍率
    actual_total = sum(new_durs)
    if actual_total > 0:
        actual_speed = round(total_dur_ms / actual_total, 1)
    else:
        actual_speed = speed
    warning = (
        f"ℹ️ GIF 调速：原 {frame_count} 帧 / {original_avg_fps:.1f} FPS，"
        f"×{speed} 需丢帧\n"
        f"每 {keep_every} 帧保留 1 帧（→ {len(kept_frames)} 帧），"
        f"实际倍率 ≈ ×{actual_speed}。"
    )

    return output_path, speed, warning
