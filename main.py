"""图片处理工具箱：反色、调速、@用户反色（参照 pic_mirror 的指令解析模式）"""

import asyncio
import os
import re
import tempfile
from PIL import Image

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.event.filter import EventMessageType
from astrbot.api.star import Context, Star

from . import gif_speed, invert, flip, petpet

QQ_AVATAR_URL = "http://q1.qlogo.cn/g?b=qq&nk={qq}&s=640"

# ── 工具函数 ────────────────────────────────────

def _download_sync(url: str, path: str) -> bool:
    import requests
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "AstrBot/pic_toolbox"})
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        logger.error(f"[pic_toolbox] 下载失败: {e}")
        return False

def _is_gif(path: str) -> bool:
    try:
        with Image.open(path) as im:
            return getattr(im, "is_animated", False)
    except Exception:
        return path.lower().endswith(".gif")


# ── 插件主体 ─────────────────────────────────────

class PicToolboxPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        if config is None:
            config = {}
        self._enable_at_avatar = config.get("enable_at_avatar", True)
        self._match_mode = config.get("match_mode", False)

    # ── 参照 pic_mirror 的指令解析 ─────────────
    @filter.event_message_type(EventMessageType.ALL)
    async def handle_all_commands(self, event: AstrMessageEvent):
        """手动解析 @用户 指令 或 指令 @用户，避免 / 前缀和 @ 标记冲突。"""
        msg = event.message_str.strip()

        # 解析指令和 @ 目标（参照 pic_mirror 两阶段解析）
        actual_cmd = msg
        at_qq = self._extract_at_qq(event)

        if " @" in msg:
            parts = msg.split("@", 1)
            actual_cmd = parts[0].strip()
        elif msg.startswith("@"):
            parts = msg.split(None, 2)
            if len(parts) >= 2:
                actual_cmd = parts[1].strip()

        # 去掉可能的前导 /
        cmd_text = actual_cmd.lstrip("/").strip()

        # ── 反色 ────────────────────────────
        if cmd_text == "反色":
            image_url = None

            # 头像：@用户
            if at_qq and self._enable_at_avatar:
                image_url = QQ_AVATAR_URL.format(qq=at_qq)

            # 引用/直接图片
            if not image_url:
                image_url = self._extract_image_url(event)

            if not image_url:
                return

            event.stop_event()
            async for r in self._download_and_process(event, image_url, invert.invert_image, "反色"):
                yield r
            return

        # ── 左右翻转 ─────────────────────────
        if cmd_text == "左右翻转":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return

            image_url = None
            if at_qq and self._enable_at_avatar:
                image_url = QQ_AVATAR_URL.format(qq=at_qq)
            if not image_url:
                image_url = self._extract_image_url(event)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, flip.flip_horizontal, "左右翻转"):
                yield r
            return

        # ── 上下翻转 ─────────────────────────
        if cmd_text == "上下翻转":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return

            image_url = None
            if at_qq and self._enable_at_avatar:
                image_url = QQ_AVATAR_URL.format(qq=at_qq)
            if not image_url:
                image_url = self._extract_image_url(event)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, flip.flip_vertical, "上下翻转"):
                yield r
            return

        # ── 摸头 ────────────────────────────
        if cmd_text == "摸头":
            if not self._match_mode and not actual_cmd.startswith("/"):
                return

            image_url = None
            if at_qq and self._enable_at_avatar:
                image_url = QQ_AVATAR_URL.format(qq=at_qq)
            if not image_url:
                image_url = self._extract_image_url(event)
            if not image_url:
                return
            event.stop_event()
            async for r in self._download_and_process(event, image_url, petpet.generate_petpet, "摸头"):
                yield r
            return

        # ── 调速（需精准匹配模式 或 显式 /）──
        speed_match = re.match(r"^调速\s+([\d.]+)$", actual_cmd)
        if speed_match:
            if not self._match_mode and not actual_cmd.startswith("/"):
                return
            image_url = self._extract_image_url(event)
            if not image_url:
                return
            try:
                speed = gif_speed.parse_speed(speed_match.group(1))
            except ValueError as e:
                yield event.plain_result(str(e))
                return
            event.stop_event()
            def proc(inp, out):
                gif_speed.adjust_gif_speed(inp, out, speed)
            async for r in self._download_and_process(event, image_url, proc, "调速"):
                yield r

    # ── 从组件提取 ────────────────────────────
    @staticmethod
    def _extract_at_qq(event: AstrMessageEvent) -> str | None:
        for comp in event.get_messages():
            if isinstance(comp, Comp.At):
                for attr in ("qq", "target", "user_id", "id"):
                    qq = getattr(comp, attr, None)
                    if qq:
                        return str(qq)
        return None

    @staticmethod
    def _extract_image_url(event: AstrMessageEvent) -> str | None:
        for comp in event.get_messages():
            if isinstance(comp, Comp.Reply):
                chain = getattr(comp, "chain", None) or []
                for rc in chain:
                    if isinstance(rc, Comp.Image):
                        url = getattr(rc, "url", None) or getattr(rc, "file", None)
                        if url:
                            return url
        for comp in event.get_messages():
            if isinstance(comp, Comp.Image):
                url = getattr(comp, "url", None) or getattr(comp, "file", None)
                if url:
                    return url
        return None

    async def _download_and_process(self, event: AstrMessageEvent,
                                     image_url: str, processor, label: str):
        input_path = os.path.join(tempfile.gettempdir(), f"pt_in_{os.getpid()}.tmp")
        loop = asyncio.get_event_loop()
        ok = await loop.run_in_executor(None, _download_sync, image_url, input_path)
        if not ok:
            yield event.plain_result("图片下载失败，请稍后重试。")
            return

        ext = ".gif" if _is_gif(input_path) else ".png"
        output_path = os.path.join(tempfile.gettempdir(), f"pt_out_{os.getpid()}{ext}")

        try:
            processor(input_path, output_path)
        except Exception as e:
            logger.error(f"[pic_toolbox] {label} 失败: {e}")
            yield event.plain_result(f"处理失败: {e}")
            return
        finally:
            try:
                os.remove(input_path)
            except OSError:
                pass

        yield event.chain_result([Comp.Image(file=str(output_path))])
        async def _cleanup():
            await asyncio.sleep(30)
            try:
                os.remove(output_path)
            except OSError:
                pass
        asyncio.ensure_future(_cleanup())

    async def terminate(self):
        pass
