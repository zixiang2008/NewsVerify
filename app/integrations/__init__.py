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


class GenericWebhookChannel(BaseChannel):
    """Config-driven outbound channel for webhook-based platforms.

    Builds the platform-specific JSON body (Feishu / DingTalk / WeCom / Slack /
    Discord / LINE / generic) from stored credentials so a single test button
    verifies the real integration format, not a generic placeholder.
    """

    def __init__(self, key: str, label: str, webhook_url: str = "", secret: str = "", credentials: dict | None = None):
        self.key = key
        self.label = label
        self.credentials = dict(credentials or {})
        self.webhook_url = webhook_url or self.credentials.get("webhook_url", "")
        self.secret = secret or self.credentials.get("signing_secret", "")
        self.configured = bool(webhook_url or self.credentials.get("webhook_url")
                               or self.credentials.get("channel_access_token")
                               or self.credentials.get("access_token")
                               or self.credentials.get("app_id"))

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

    def _payload(self, text: str) -> tuple[Dict[str, Any], Dict[str, str]]:
        """Return (json body, extra headers) for the platform's webhook format."""
        c = self.credentials
        if self.key == "feishu":
            body: Dict[str, Any] = {"msg_type": "text", "content": {"text": text}}
            secret = c.get("signing_secret") or self.secret
            if secret:
                import time, hashlib, base64
                ts = str(int(time.time()))
                s = f"{ts}\n{secret}".encode()
                h = base64.b64encode(hashlib.sha256(s).digest()).decode()
                body["timestamp"] = ts
                body["sign"] = h
            return body, {}
        if self.key == "dingtalk":
            body = {"msgtype": "text", "text": {"content": text}}
            secret = c.get("signing_secret") or self.secret
            if secret:
                import time, hashlib, base64, urllib.parse, hmac
                ts = str(int(time.time() * 1000))
                sign_str = f"{ts}\n{secret}"
                code = base64.b64encode(
                    hmac.new(secret.encode(), sign_str.encode(), hashlib.sha256).digest()
                ).decode()
                body["timestamp"] = ts
                body["sign"] = urllib.parse.quote_plus(code)
            return body, {}
        if self.key == "wecom":
            return {"msgtype": "text", "text": {"content": text}}, {}
        if self.key == "discord":
            return {"content": text}, {}
        if self.key == "slack":
            return {"text": text}, {}
        if self.key == "line":
            return {"messages": [{"type": "text", "text": text}]}, {
                "Authorization": f"Bearer {c.get('channel_access_token', '')}"
            }
        return {"text": text, "chat_id": ""}, {}

    async def send_message(self, chat_id: str, reply: IMReply) -> bool:
        if not self.configured:
            return False
        try:
            import httpx
            body, headers = self._payload(reply.text[:4000])
            async with httpx.AsyncClient(timeout=15) as c:
                if self.webhook_url:
                    r = await c.post(self.webhook_url, json=body, headers=headers)
                    return r.status_code < 300
                if self.key == "line" and self.credentials.get("channel_access_token"):
                    r = await c.post("https://api.line.me/v2/bot/message/broadcast", json=body, headers=headers)
                    return r.status_code < 300
                if self.key == "matrix":
                    hs = str(self.credentials.get("homeserver", "")).rstrip("/")
                    room = self.credentials.get("room_id") or chat_id
                    if not hs or not room:
                        return False
                    r = await c.post(
                        f"{hs}/_matrix/client/v3/rooms/{room}/send/m.room.message",
                        headers={"Authorization": f"Bearer {self.credentials.get('access_token', '')}"},
                        json={"msgtype": "m.text", "body": reply.text[:4000]},
                    )
                    return r.status_code < 300
            return False
        except Exception:
            return False


class TelegramChannel(BaseChannel):
    key = "telegram"
    label = "Telegram"

    def __init__(self, credentials: dict | None = None):
        from app.core.config import get_settings
        c = dict(credentials or {})
        self.token = c.get("bot_token") or get_settings().telegram_bot_token or ""
        ids = c.get("allowed_user_ids")
        if ids is None:
            self.allowed = set(get_settings().allowed_user_ids())
        else:
            self.allowed = {int(x.strip()) for x in str(ids).split(",") if x.strip().isdigit()}
        self.configured = bool(self.token)

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


def get_settings_value(env_name: str) -> str:
    """Read a setting from env lazily (avoids import-time Settings caching)."""
    import os
    return os.getenv(env_name, "")


def build_channel(key: str, credentials: dict | None, label: str = "") -> BaseChannel | None:
    c = dict(credentials or {})
    if key == "telegram":
        return TelegramChannel(c)
    if key in CHANNEL_CATALOGUE_KEYS:
        return GenericWebhookChannel(key, label or key, credentials=c)
    return None


CHANNEL_CATALOGUE_KEYS = {
    "discord", "slack", "feishu", "dingtalk", "wecom", "wechat_oa",
    "qq_onebot", "line", "matrix", "generic",
}


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
        self._db_credentials: Dict[str, dict] = {}

    def bootstrap(self) -> None:
        if self._bootstrapped:
            return
        self._bootstrapped = True
        self.rebuild()

    def rebuild(self) -> None:
        """(Re)build channels from DB credentials with env fallback.

        Called at startup and again whenever the admin wizard saves a channel,
        so edits take effect immediately without a container restart.
        """
        import os
        self._channels.clear()
        for ch in CHANNEL_CATALOGUE:
            key, label = ch["key"], ch["label"]
            db_creds = self._db_credentials.get(key, {})
            if key == "telegram":
                creds = dict(db_creds)
                if not creds.get("bot_token"):
                    creds["bot_token"] = get_settings_value("TELEGRAM_BOT_TOKEN")
                self._channels[key] = TelegramChannel(creds)
            else:
                creds = dict(db_creds)
                if not creds.get("webhook_url"):
                    creds["webhook_url"] = os.getenv(f"NV_IM_{key.upper()}_WEBHOOK", "")
                if not creds.get("signing_secret"):
                    creds["signing_secret"] = os.getenv(f"NV_IM_{key.upper()}_SECRET", "")
                self._channels[key] = GenericWebhookChannel(key, label, credentials=creds)

    async def reload_from_db(self) -> None:
        from app.integrations.channel_store import load_all_raw
        self._db_credentials = await load_all_raw()
        self._bootstrapped = True
        self.rebuild()

    def set_db_credentials(self, key: str, credentials: dict) -> None:
        self._db_credentials[key] = dict(credentials)
        self._bootstrapped = True
        self.rebuild()

    def remove_db_credentials(self, key: str) -> None:
        self._db_credentials.pop(key, None)
        self._bootstrapped = True
        self.rebuild()

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
