"""Unified instant-messaging adapter layer for NewsVerify.

Design inspired by mature multi-channel bot frameworks (NoneBot / OneBot,
Kirara AI / chatgpt-on-wechat): a config-driven registry of platform adapters
that normalise inbound messages and outbound replies behind one interface.

This module is the *abstraction*. It defines the contract every channel must
implement and a dispatcher that forwards normalised messages to NewsVerify's
verification pipeline. Credentials are read from environment/settings and are
never hard-coded. No login/paywall/anti-bot bypass is performed.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class IMMessage:
    channel: str
    chat_id: str
    user_id: str
    text: str
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IMReply:
    text: str
    parse_mode: str = "plain"


class BaseChannel(ABC):
    """Contract for one instant-messaging platform adapter."""

    key: str = "base"
    label: str = "Base"
    configured: bool = False

    @abstractmethod
    async def parse_inbound(self, payload: Dict[str, Any], signature: str = "") -> Optional[IMMessage]:
        """Turn a platform webhook payload into a normalised message."""

    @abstractmethod
    async def send_message(self, chat_id: str, reply: IMReply) -> bool:
        """Send a reply back to the platform."""

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        return True  # overridden by channels that require signed webhooks


class TelegramChannel(BaseChannel):
    key = "telegram"
    label = "Telegram"

    def __init__(self):
        from app.core.config import get_settings
        self.token = get_settings().telegram_bot_token or ""
        self.configured = bool(self.token)
        self.allowed = set(get_settings().allowed_user_ids())

    async def parse_inbound(self, payload: Dict[str, Any], signature: str = "") -> Optional[IMMessage]:
        msg = payload.get("message") or payload.get("edited_message")
        if not msg:
            return None
        chat = msg.get("chat", {})
        user = msg.get("from", {})
        text = msg.get("text", "")
        if not text:
            return None
        if self.allowed and user.get("id") not in self.allowed:
            return None
        return IMMessage(self.key, str(chat.get("id", "")), str(user.get("id", "")), text, payload)

    async def send_message(self, chat_id: str, reply: IMReply) -> bool:
        if not self.configured:
            return False
        try:
            import httpx
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(url, json={"chat_id": chat_id, "text": reply.text[:4000]})
                return r.status_code == 200
        except Exception:
            return False


class GenericWebhookChannel(BaseChannel):
    """Generic channel for Slack / Discord / Feishu / DingTalk / WeCom / LINE etc.

    Inbound: platforms post a normalised JSON body
      {"chat_id": "...", "user_id": "...", "text": "..."}
    Outbound: a configurable webhook URL receives {"text": "..."}.
    This keeps the adapter open-ended so any mainstream IM can be connected by
    configuration alone, without forking the app.
    """

    def __init__(self, key: str, label: str, webhook_url: str = "", secret: str = ""):
        self.key = key
        self.label = label
        self.webhook_url = webhook_url
        self.secret = secret
        self.configured = bool(webhook_url)

    async def parse_inbound(self, payload: Dict[str, Any], signature: str = "") -> Optional[IMMessage]:
        # Accept both a normalised body and common platform shapes.
        text = payload.get("text")
        if text is None:
            for k in ("content", "message", "question", "prompt"):
                if k in payload:
                    text = payload[k]
                    break
        if isinstance(text, dict):
            text = text.get("text") or text.get("content")
        if not text:
            return None
        chat_id = str(payload.get("chat_id") or payload.get("channel_id") or payload.get("chatId") or "web")
        user_id = str(payload.get("user_id") or payload.get("userId") or "unknown")
        return IMMessage(self.key, chat_id, user_id, str(text), payload)

    async def send_message(self, chat_id: str, reply: IMReply) -> bool:
        if not self.webhook_url:
            return False
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(self.webhook_url, json={"text": reply.text[:4000], "chat_id": chat_id})
                return r.status_code < 300
        except Exception:
            return False


# Mainstream IM catalogue — adapters are config-driven from settings/env.
CHANNEL_CATALOGUE: List[Dict[str, str]] = [
    {"key": "telegram", "label": "Telegram", "docs": "https://core.telegram.org/bots/api"},
    {"key": "discord", "label": "Discord", "docs": "https://discord.com/developers/docs"},
    {"key": "slack", "label": "Slack", "docs": "https://api.slack.com/"},
    {"key": "feishu", "label": "飞书 Feishu / Lark", "docs": "https://open.feishu.cn/"},
    {"key": "dingtalk", "label": "钉钉 DingTalk", "docs": "https://open.dingtalk.com/"},
    {"key": "wecom", "label": "企业微信 WeCom", "docs": "https://developer.work.weixin.qq.com/"},
    {"key": "wechat_oa", "label": "微信公众号", "docs": "https://developers.weixin.qq.com/officialAccount/"},
    {"key": "qq_onebot", "label": "QQ / OneBot", "docs": "https://onebot.dev/"},
    {"key": "line", "label": "LINE", "docs": "https://developers.line.biz/"},
    {"key": "matrix", "label": "Matrix", "docs": "https://matrix.org/docs/"},
    {"key": "generic", "label": "通用 Webhook / 自定义", "docs": "自定义 HTTP 回调接入"},
]


class ChannelRegistry:
    def __init__(self):
        self._channels: Dict[str, BaseChannel] = {}
        self._handler: Optional[Callable[[IMMessage], Any]] = None
        self._bootstrapped = False

    def bootstrap(self) -> None:
        if self._bootstrapped:
            return
        self._bootstrapped = True
        self._channels["telegram"] = TelegramChannel()
        # Optional webhook channels are configured via env: NV_IM_{KEY}_WEBHOOK
        import os
        for ch in CHANNEL_CATALOGUE:
            key = ch["key"]
            if key == "telegram":
                continue
            url = os.getenv(f"NV_IM_{key.upper()}_WEBHOOK", "")
            secret = os.getenv(f"NV_IM_{key.upper()}_SECRET", "")
            self._channels[key] = GenericWebhookChannel(key, ch["label"], url, secret)

    def set_handler(self, handler: Callable[[IMMessage], Any]) -> None:
        self._handler = handler

    def get(self, key: str) -> Optional[BaseChannel]:
        self.bootstrap()
        return self._channels.get(key)

    def catalogue(self) -> List[Dict[str, Any]]:
        self.bootstrap()
        out = []
        for ch in CHANNEL_CATALOGUE:
            c = self._channels.get(ch["key"])
            out.append({**ch, "configured": bool(c and c.configured)})
        return out

    async def dispatch(self, key: str, payload: Dict[str, Any], signature: str = "") -> Optional[str]:
        ch = self.get(key)
        if not ch:
            return None
        msg = await ch.parse_inbound(payload, signature)
        if not msg or not msg.text:
            return None
        if self._handler:
            result = self._handler(msg)
            if asyncio.iscoroutine(result):
                reply = await result
            else:
                reply = result
            if isinstance(reply, IMReply):
                return reply.text
        return None


registry = ChannelRegistry()
