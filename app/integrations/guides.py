"""Interactive setup metadata for mainstream instant-messaging platforms.

Design reference: AstrBot / NoneBot / Koishi adapter ecosystems — a config-driven
adapter registry with a WebUI向导. This module only describes *how to connect*
each platform; it never bypasses login, paywalls or anti-bot protections.

Two connection modes are supported:
  * ``webhook`` — platform posts to our unified inbound URL (Feishu, DingTalk,
    WeCom, Slack, Discord, LINE, Matrix, generic). User only pastes a token /
    signing secret; no code, no restart.
  * ``token`` — we call the platform Bot API to send (Telegram). User pastes a
    bot token obtained from the platform's official bot manager.

QR binding: Telegram supports scanning a t.me deep link to open a chat with the
bot; Feishu/DingTalk/WeCom/LINE provide official QR codes in their admin panels.
We surface the official deep link / QR entry plus a one-click copy of our inbound
URL, and let the user verify with a real test message.
"""

from __future__ import annotations

from typing import Any, Dict, List


def _field(name: str, label: str, kind: str = "text", *, placeholder: str = "",
           help: str = "", required: bool = False, secret: bool = False) -> Dict[str, Any]:
    return {
        "name": name, "label": label, "kind": kind, "placeholder": placeholder,
        "help": help, "required": required, "secret": secret,
    }


# Unified inbound webhook path (host is filled by the UI from window.location).
INBOUND_PATH = "/api/v1/im/{key}/webhook"

CHANNEL_GUIDES: Dict[str, Dict[str, Any]] = {
    "telegram": {
        "label": "Telegram", "icon": "✈️", "mode": "token",
        "summary": "官方 BotFather 创建机器人，粘贴 Token 即可；支持扫码打开对话一键绑定。",
        "docs": "https://core.telegram.org/bots/features#creating-a-new-bot",
        "connect_url": "https://t.me/BotFather",
        "qr": {
            "supported": True,
            "kind": "deeplink",
            "hint": "保存后点「生成绑定二维码」，手机扫码打开机器人并发送 /start，即可绑定会话。",
            "template": "https://t.me/{bot_username}",
        },
        "fields": [
            _field("bot_token", "Bot Token", "password", placeholder="123456:ABC...",
                   help="在 BotFather 发送 /newbot 后获得；留空则沿用已保存值", required=True, secret=True),
            _field("bot_username", "机器人用户名", "text", placeholder="YourNewsBot",
                   help="用于生成扫码深链（不带 @）"),
            _field("allowed_user_ids", "允许的用户 ID", "text", placeholder="123456,789012",
                   help="逗号分隔，留空表示允许所有人；建议填写自己的 ID"),
        ],
        "steps": [
            "手机或网页打开 @BotFather，发送 /newbot",
            "按提示设置名称与用户名，复制返回的 Token",
            "把 Token 粘贴到下方表单并保存",
            "点击「生成绑定二维码」，扫码打开机器人并发送 /start",
            "点「发送测试消息」，收到即接入成功",
        ],
    },
    "discord": {
        "label": "Discord", "icon": "🎮", "mode": "webhook",
        "summary": "在服务器频道创建 Webhook（或机器人），粘贴地址即可接收与回复。",
        "docs": "https://discord.com/developers/docs/resources/webhook",
        "connect_url": "https://discord.com/developers/applications",
        "qr": {"supported": False, "kind": "official",
               "hint": "官方在「服务器设置 → 集成 → Webhook」中提供创建入口；创建后把 URL 粘贴到下方。"},
        "fields": [
            _field("webhook_url", "Webhook URL", "url", placeholder="https://discord.com/api/webhooks/...",
                   help="频道 → 编辑频道 → 集成 → Webhook → 新建 Webhook，复制 URL", required=True),
        ],
        "steps": [
            "打开 Discord 开发者门户或直接到目标频道的「集成 → Webhook」",
            "新建 Webhook，复制 Webhook URL",
            "粘贴到下方表单并保存",
            "点「发送测试消息」，频道收到即接入成功",
        ],
    },
    "slack": {
        "label": "Slack", "icon": "💬", "mode": "webhook",
        "summary": "创建 Incoming Webhook 应用，粘贴地址即可；签名密钥可选。",
        "docs": "https://api.slack.com/messaging/webhooks",
        "connect_url": "https://api.slack.com/apps",
        "qr": {"supported": False, "kind": "official",
               "hint": "在 Slack App 目录搜索 “Incoming Webhooks” 创建应用，官方页面会给出配置二维码/链接。"},
        "fields": [
            _field("webhook_url", "Webhook URL", "url", placeholder="https://hooks.slack.com/services/...",
                   help="启用 Incoming Webhooks 后复制生成的 URL", required=True),
            _field("signing_secret", "Signing Secret（可选）", "password",
                   help="用于校验入站请求签名；在 App 的 Basic Information 中获取", secret=True),
        ],
        "steps": [
            "打开 Slack App 目录，创建 Incoming Webhook 应用并选择频道",
            "复制 Webhook URL（可选：复制 Signing Secret）",
            "粘贴到下方表单并保存",
            "点「发送测试消息」，频道收到即接入成功",
        ],
    },
    "feishu": {
        "label": "飞书 Feishu / Lark", "icon": "🪶", "mode": "webhook",
        "summary": "群机器人自定义 Webhook，粘贴地址即可；支持加签校验。",
        "docs": "https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot",
        "connect_url": "https://open.feishu.cn/",
        "qr": {"supported": True, "kind": "official",
               "hint": "飞书群设置 → 群机器人 → 添加机器人，官方弹窗会展示二维码；添加后复制 Webhook 地址。"},
        "fields": [
            _field("webhook_url", "机器人 Webhook 地址", "url",
                   placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/...",
                   help="群设置 → 群机器人 → 添加自定义机器人后复制", required=True),
            _field("signing_secret", "加签密钥（可选）", "password",
                   help="若开启签名校验，填写 secret（不含 “签” 前缀）", secret=True),
        ],
        "steps": [
            "在飞书群中打开「设置 → 群机器人 → 添加机器人 → 自定义机器人」",
            "按官方弹窗扫码/确认，安全设置建议勾选签名校验",
            "复制 Webhook 地址（及加签密钥）到下方表单并保存",
            "点「发送测试消息」，群里收到即接入成功",
        ],
    },
    "dingtalk": {
        "label": "钉钉 DingTalk", "icon": "📌", "mode": "webhook",
        "summary": "群自定义机器人 Webhook，支持加签；粘贴地址即可。",
        "docs": "https://open.dingtalk.com/document/robots/custom-robot-access",
        "connect_url": "https://open.dingtalk.com/",
        "qr": {"supported": True, "kind": "official",
               "hint": "钉钉群设置 → 智能群助手 → 添加机器人 → 自定义，官方提供二维码确认；完成后复制 Webhook。"},
        "fields": [
            _field("webhook_url", "机器人 Webhook 地址", "url",
                   placeholder="https://oapi.dingtalk.com/robot/send?access_token=...",
                   help="群 → 设置 → 智能群助手 → 自定义机器人，复制地址", required=True),
            _field("signing_secret", "加签密钥（可选）", "password",
                   help="若选择「加签」安全方式，填写 SEC 后面的密钥", secret=True),
        ],
        "steps": [
            "钉钉群设置 → 智能群助手 → 添加机器人 → 自定义",
            "设置名称与安全方式（推荐加签），按提示扫码确认",
            "复制 Webhook 地址与加签密钥到下方表单并保存",
            "点「发送测试消息」，群里收到即接入成功",
        ],
    },
    "wecom": {
        "label": "企业微信 WeCom", "icon": "🏢", "mode": "webhook",
        "summary": "群机器人 Webhook，粘贴地址即可；无需重启服务。",
        "docs": "https://developer.work.weixin.qq.com/document/path/91770",
        "connect_url": "https://work.weixin.qq.com/",
        "qr": {"supported": True, "kind": "official",
               "hint": "企业微信群 → 群设置 → 群机器人 → 添加机器人，官方弹窗展示二维码。"},
        "fields": [
            _field("webhook_url", "机器人 Webhook 地址", "url",
                   placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=...",
                   help="群设置 → 群机器人 → 添加机器人后复制地址", required=True),
        ],
        "steps": [
            "在企业微信群中打开「群设置 → 群机器人 → 添加机器人」",
            "按官方提示扫码确认并创建，复制 Webhook 地址",
            "粘贴到下方表单并保存",
            "点「发送测试消息」，群里收到即接入成功",
        ],
    },
    "wechat_oa": {
        "label": "微信公众号", "icon": "💚", "mode": "webhook",
        "summary": "在公众号后台配置服务器地址与 Token，粘贴到下方即可完成对接。",
        "docs": "https://developers.weixin.qq.com/doc/offiaccount/Getting_Started/Overview.html",
        "connect_url": "https://mp.weixin.qq.com/",
        "qr": {"supported": False, "kind": "official",
               "hint": "公众号后台「设置与开发 → 基本配置」可查看 AppID，并用开发者工具扫码验证。"},
        "fields": [
            _field("app_id", "AppID", "text", help="公众号后台 → 设置与开发 → 基本配置", required=True),
            _field("app_secret", "AppSecret", "password", help=" basic 配置中获取，仅在保存时使用", secret=True),
            _field("verify_token", "服务器配置 Token", "password",
                   help="公众号后台「服务器配置」里自定义的 Token", secret=True),
        ],
        "steps": [
            "打开公众号后台 → 设置与开发 → 基本配置，获取 AppID / AppSecret",
            "在「服务器配置」中设置 Token（自定义字符串）",
            "把本页显示的接收 URL 填入公众号后台的 URL 栏（_encodingAESKey 可留空选明文模式）",
            "把 AppID / AppSecret / Token 填到下方表单保存，再点测试",
        ],
    },
    "qq_onebot": {
        "label": "QQ / OneBot", "icon": "🐧", "mode": "webhook",
        "summary": "需配合 OneBot 实现（NapCat / Lagrange），在客户端扫码登录 QQ 后粘贴上报地址。",
        "docs": "https://onebot.dev/",
        "connect_url": "https://github.com/NapNeko/NapCatQQ",
        "qr": {"supported": True, "kind": "official",
               "hint": "OneBot 客户端（如 NapCat）启动时会展示 QQ 登录二维码，扫码即可登录绑定。"},
        "fields": [
            _field("webhook_url", "OneBot 上报地址", "url",
                   placeholder="http://127.0.0.1:3000/onebot/webhook",
                   help="在 NapCat/Lagrange 中配置 HTTP 上报地址指向本系统接收 URL", required=True),
            _field("access_token", "Access Token（可选）", "password",
                   help="OneBot 客户端设置的鉴权 Token", secret=True),
        ],
        "steps": [
            "在 NAS 部署 OneBot 客户端（NapCat / Lagrange），启动后扫码登录 QQ",
            "在客户端配置 HTTP 上报地址为本页显示的接收 URL",
            "把上报地址与 Token 填到下方表单保存",
            "点「发送测试消息」验证回执",
        ],
    },
    "line": {
        "label": "LINE", "icon": "🟢", "mode": "webhook",
        "summary": "LINE Developers 创建 Provider/Channel，粘贴 Channel Token 与 Secret。",
        "docs": "https://developers.line.biz/en/docs/messaging-api/overview/",
        "connect_url": "https://developers.line.biz/console/",
        "qr": {"supported": True, "kind": "official",
               "hint": "LINE Developers 控制台频道页提供「Add friend」二维码，扫码即可把机器人加为好友。"},
        "fields": [
            _field("channel_access_token", "Channel Access Token", "password",
                   help="LINE Developers → Messaging API → Issued token", required=True, secret=True),
            _field("channel_secret", "Channel Secret", "password",
                   help="频道 Basic settings 中获取", secret=True),
        ],
        "steps": [
            "在 LINE Developers 创建 Provider 与 Messaging API Channel",
            "在 Basic settings 复制 Channel Secret，在 Messaging API 签发 Channel Access Token",
            "把接收 URL 填入 Webhook URL 并开启 Use webhook",
            "把 Token / Secret 填到下方表单保存，扫码加好友后点测试",
        ],
    },
    "matrix": {
        "label": "Matrix", "icon": "🧩", "mode": "webhook",
        "summary": "使用 homeserver 的 Access Token 通过标准 API 收发消息。",
        "docs": "https://matrix.org/docs/api/client-server/",
        "connect_url": "https://matrix.org/docs/api/client-server/",
        "qr": {"supported": False, "kind": "official",
               "hint": "Matrix 客户端（Element）登录后在设置中查看 homeserver 与 Access Token。"},
        "fields": [
            _field("homeserver", "Homeserver", "url", placeholder="https://matrix.example.org",
                   help="你的 Matrix 服务器地址", required=True),
            _field("access_token", "Access Token", "password", help="客户端登录后获取", required=True, secret=True),
            _field("room_id", "默认房间 ID", "text", placeholder="!xxxxx:example.org",
                   help="用于发送测试消息的房间"),
        ],
        "steps": [
            "在 Element 等客户端登录你的 Matrix 账号",
            "在设置中获取 homeserver 地址与 Access Token",
            "填入下方表单（room_id 用于测试消息）并保存",
            "点「发送测试消息」验证",
        ],
    },
    "generic": {
        "label": "通用 Webhook / 自定义", "icon": "🔌", "mode": "webhook",
        "summary": "任何支持 HTTP Webhook 的系统都能对接，填入目标地址即可。",
        "docs": "",
        "connect_url": "",
        "qr": {"supported": False, "kind": "none", "hint": "自定义系统按你的平台说明配置即可。"},
        "fields": [
            _field("webhook_url", "目标 Webhook URL", "url", placeholder="https://example.com/hook",
                   help="测试消息将发送到该地址", required=True),
            _field("signing_secret", "签名密钥（可选）", "password", help="用于校验入站请求", secret=True),
        ],
        "steps": [
            "确认接收方支持 HTTP POST JSON",
            "把目标 Webhook URL 填入下方表单并保存",
            "点「发送测试消息」，目标地址收到 JSON 即接入成功",
        ],
    },
}


def guide(key: str) -> Dict[str, Any] | None:
    return CHANNEL_GUIDES.get(key)


def public_catalogue() -> List[Dict[str, Any]]:
    """Guide data safe to return to the browser (no credentials)."""
    out: List[Dict[str, Any]] = []
    for key, g in CHANNEL_CATALOGUE_ORDER:
        g = dict(g)
        g["key"] = key
        out.append(g)
    return out


# Preserve catalogue order; imported lazily to avoid circular import at module load.
from app.integrations import CHANNEL_CATALOGUE as _CATALOGUE  # noqa: E402

CHANNEL_CATALOGUE_ORDER = [(c["key"], CHANNEL_GUIDES.get(c["key"], {})) for c in _CATALOGUE]
