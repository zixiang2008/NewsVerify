from __future__ import annotations

import json
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.db.session import get_sessionmaker
from app.core.config import get_settings
from app.version import VERSION, RELEASE_DATE, CODENAME, version_payload
from app.verification.top_media import TOP_MEDIA, NOTE
from app.verification.source_policy import classify_source
from app.integrations import registry as im_registry, CHANNEL_CATALOGUE
from app.integrations import IMMessage, IMReply
from app.integrations.guides import CHANNEL_GUIDES, public_catalogue
from app.integrations import channel_store
from app.web.mindmap_asset import CSS as MM_CSS, JS as MM_JS, share_page as mm_share_page
from app.web.design import DESIGN_CSS, THEME_CSS, page_shell, tabs_html, SHELL_JS
from app.web import auth as nv_auth
from app.web.auth_pages import login_page as auth_login_html, register_page as auth_register_html, admin_login_page as auth_admin_login_html
from app.web.admin_pages import overview_page, accounts_page
from app.web.api_console import api_console_page
from app.web.api_process import build_process
from fastapi import Depends, HTTPException

API_SETTING_DEFAULTS = {
    "api_enabled": True,
    "allow_write": True,
    "max_results": 100,
    "rate_limit_per_min": 120,
    "public_base_url": "",
    "agent_note": "通过 X-API-Key 请求头携带管理 Key；先 GET /api/v1/status 验证连通。",
}


async def get_api_settings() -> dict:
    """Runtime API settings with safe defaults, read from the database."""
    from sqlalchemy import select
    from app.db.models import ApiSetting
    out = dict(API_SETTING_DEFAULTS)
    try:
        sm = get_sessionmaker()
        async with sm() as session:
            rows = (await session.execute(select(ApiSetting))).scalars().all()
            for row in rows:
                if isinstance(row.value, dict) and "value" in row.value:
                    out[row.key] = row.value["value"]
    except Exception:
        pass
    return out


async def verify_api_key(request: Request):
    """Key authentication for the public /api/v1 surface.

    Managed keys live in the database (created by a super admin). The legacy
    ``API_KEY`` environment variable remains a valid fallback.
    """
    import os
    from sqlalchemy import select
    from app.db.models import ApiKey, now_utc

    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not key:
        raise HTTPException(status_code=401, detail="missing API key")
    settings = await get_api_settings()
    if not settings.get("api_enabled", True):
        raise HTTPException(status_code=503, detail="API temporarily disabled by administrator")

    try:
        sm = get_sessionmaker()
        async with sm() as session:
            result = await session.execute(select(ApiKey).where(ApiKey.key == key))
            rec = result.scalars().first()
            if rec:
                if not rec.enabled:
                    raise HTTPException(status_code=403, detail="API key disabled")
                scopes = list(rec.scopes or ["read"])
                write_call = request.method in ("POST", "PUT", "PATCH", "DELETE")
                if write_call and not settings.get("allow_write", True):
                    raise HTTPException(status_code=403, detail="write operations disabled")
                if write_call and not ({"write", "admin"} & set(scopes)):
                    raise HTTPException(status_code=403, detail="key lacks write scope")
                rec.calls = (rec.calls or 0) + 1
                rec.last_used_at = now_utc()
                await session.commit()
                request.state.api_key = {"key": key, "name": rec.name, "scopes": scopes}
                return True
    except HTTPException:
        raise
    except Exception:
        pass

    expected = os.getenv("API_KEY", "") or getattr(get_settings(), "api_key", "")
    if expected and key == expected:
        request.state.api_key = {"key": key, "name": "legacy env key", "scopes": ["read", "write", "admin"]}
        return True
    raise HTTPException(status_code=401, detail="invalid API key")


app = FastAPI(title="NewsVerify", version=VERSION)


@app.on_event("startup")
async def _load_im_channels():
    """Load wizard-saved credentials and seed the built-in administrators."""
    try:
        await nv_auth.seed_super_admins(get_sessionmaker())
    except Exception as exc:
        print("admin seed failed:", exc)
    try:
        app.state.public_base_url = (await get_api_settings()).get("public_base_url", "") or ""
    except Exception:
        pass
    try:
        await im_registry.reload_from_db()
    except Exception:
        pass


# 注册 IM 接入处理器：把归一化的消息路由到核查流程（此处回执确认，实际提交
# 通过 /submit 或 /api/v1/check；webhook 仅做入口抽象与白名单校验）。
def _im_handler(msg: IMMessage) -> IMReply:
    text = (msg.text or "").strip()
    if not text:
        return IMReply(text="请发送需要核查的新闻文本。")
    if len(text) > 2000:
        text = text[:2000]
    return IMReply(text=f"[{msg.label if hasattr(msg, 'label') else msg.channel}] 已收到核查请求（{len(text)} 字）。"
                        f"已进入 NewsVerify 队列；结果将按追踪约定推送。")

im_registry.set_handler(_im_handler)

ADMIN_HTML = overview_page(VERSION)

@app.middleware("http")
async def session_auth(request: Request, call_next):
    """Account session middleware.

    Public: login/registration, health, static assets, key-authenticated v1 API,
    mind-map share pages, the public theory page and the admin sign-in page.
    Everything else requires a signed ``nv_auth`` session; admin paths require
    a super-admin ``nv_admin`` session.
    """
    path = request.url.path
    public = (
        path in ("/login", "/register", "/health", "/logout", "/admin/login", "/api/admin/login")
        or path.startswith("/static")
        or path.startswith("/api/v1")
        or path.startswith("/share/")
        or (path.startswith("/api/mindmap/share/") and request.method == "GET")
        or path.startswith("/theory")
    )
    if public:
        return await call_next(request)
    if path.startswith("/admin") or path.startswith("/api/admin"):
        session = nv_auth.parse_session(request.cookies.get("nv_admin"))
        if not session or session.get("role") != "super_admin":
            if path.startswith("/api/"):
                return JSONResponse({"error": "super admin required"}, status_code=401)
            return RedirectResponse(url="/admin/login", status_code=302)
        request.state.user = session
        return await call_next(request)
    session = nv_auth.parse_session(request.cookies.get("nv_auth"))
    if not session:
        if path.startswith("/api") or path.startswith("/submit"):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return RedirectResponse(url="/login", status_code=302)
    request.state.user = session
    return await call_next(request)


def _session_response(user: dict, target: str) -> RedirectResponse:
    resp = RedirectResponse(url=target, status_code=302)
    token = nv_auth.make_session(user["username"], user["role"])
    resp.set_cookie("nv_auth", token, httponly=True, max_age=86400 * 30, samesite="lax")
    if user.get("role") == "super_admin":
        resp.set_cookie("nv_admin", token, httponly=True, max_age=86400, samesite="lax")
    return resp


@app.get("/login", response_class=HTMLResponse)
async def login_page(note: str = ""):
    return HTMLResponse(auth_login_html(VERSION, note))


@app.post("/login")
async def login_submit(username: str = Form(...), pin: str = Form(...)):
    user = await nv_auth.authenticate(get_sessionmaker(), username, pin)
    if not user:
        return RedirectResponse(url="/login?note=bad", status_code=302)
    return _session_response(user, "/")


@app.get("/register", response_class=HTMLResponse)
async def register_page(code: str = "", note: str = ""):
    return HTMLResponse(auth_register_html(VERSION, code, note))


@app.post("/register")
async def register_submit(username: str = Form(...), pin: str = Form(...), code: str = Form(...)):
    ok, message, user = await nv_auth.register_with_invite(get_sessionmaker(), username, pin, code)
    if not ok:
        note = "invite" if "邀请码" in message else ("taken" if "已被注册" in message else "invalid")
        return HTMLResponse(auth_register_html(VERSION, code, note), status_code=400)
    return RedirectResponse(url="/login?note=ok", status_code=302)


@app.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=302)
    resp.delete_cookie("nv_auth")
    resp.delete_cookie("nv_admin")
    return resp


@app.get("/theory", response_class=HTMLResponse)
async def theory_page():
    """公开的理论来源专题页。"""
    from app.web.theory import PAGE as THEORY_PAGE
    return HTMLResponse(THEORY_PAGE)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/task/{event_id}", response_class=HTMLResponse)
async def task_page(event_id: str):
    # Reuse the main page but auto-open detail via query param handled in JS
    return RedirectResponse(url=f"/?open={event_id}", status_code=302)


@app.get("/api/system")
async def api_system():
    """系统运行状况：资源消耗 + 外部 API 在线探测。"""
    from app.web.system_status import get_system_status
    return await get_system_status()


# ---------- 后台管理（超级管理员会话） ----------
@app.get("/api/admin/login")
async def admin_login_api_page():
    return HTMLResponse(auth_admin_login_html(VERSION))


@app.post("/api/admin/login")
async def admin_login_submit(request: Request):
    if request.headers.get("content-type", "").startswith("application/json"):
        body = await request.json()
        username, pin = body.get("username", ""), body.get("pin", "")
    else:
        form = await request.form()
        username, pin = form.get("username", ""), form.get("pin", "")
    user = await nv_auth.authenticate(get_sessionmaker(), username, pin)
    if not user or user.get("role") != "super_admin":
        return JSONResponse({"error": "invalid super admin credentials"}, status_code=401)
    token = nv_auth.make_session(user["username"], user["role"])
    resp = JSONResponse({"ok": True, "username": user["username"]})
    resp.set_cookie("nv_admin", token, httponly=True, max_age=86400, samesite="lax")
    resp.set_cookie("nv_auth", token, httponly=True, max_age=86400 * 30, samesite="lax")
    return resp


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_view(note: str = ""):
    return HTMLResponse(auth_admin_login_html(VERSION, note))


@app.post("/admin/login")
async def admin_login_form(username: str = Form(...), pin: str = Form(...)):
    user = await nv_auth.authenticate(get_sessionmaker(), username, pin)
    if not user or user.get("role") != "super_admin":
        return RedirectResponse(url="/admin/login?note=bad", status_code=302)
    return _session_response(user, "/admin")


@app.get("/admin", response_class=HTMLResponse)
async def admin_console():
    return HTMLResponse(ADMIN_HTML)


@app.get("/api/admin/config")
async def admin_get_config():
    """查看后台可设置信息（密钥脱敏）。"""
    s = get_settings()
    def mask(v):
        v = v or ""
        return (v[:6] + "••••" + v[-4:]) if len(v) > 10 else ("••••" if v else "")
    return {
        "llm_base_url": s.llm_base_url,
        "llm_base_url_fallback": s.llm_base_url_fallback,
        "llm_model": s.llm_model,
        "llm_judge_model": s.llm_judge_model,
        "llm_api_key_masked": mask(s.llm_api_key),
        "search_provider": s.search_provider,
        "searxng_base_url": s.searxng_base_url,
        "brave_key_masked": mask(s.brave_search_api_key),
        "google_factcheck_key_masked": mask(s.google_factcheck_api_key),
        "api_key_masked": mask(s.api_key),
        "telegram_bot_configured": bool(s.telegram_bot_token),
        "telegram_allowed_user_ids": s.telegram_allowed_user_ids,
        "custom_feed_urls": getattr(s, "custom_feed_urls", ""),
        "channels": im_registry.catalogue(),
        "version": VERSION,
        "env_notice": "修改 .env 后需重启容器生效；Webhook 接入可用下方测试入口验证。",
    }


def _public_base(request: Request) -> str:
    """Prefer the admin-configured public URL, then proxy headers, then direct URL."""
    configured = (getattr(request.app.state, "public_base_url", "") or "").strip()
    if configured:
        return configured.rstrip("/")
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    return f"{proto.split(',')[0].strip()}://{host}"


@app.get("/admin/accounts", response_class=HTMLResponse)
async def admin_accounts_page():
    return HTMLResponse(accounts_page(VERSION))


def _admin_user(request: Request) -> str:
    session = getattr(request.state, "user", None) or {}
    return str(session.get("username", "admin"))


@app.get("/api/admin/users")
async def admin_users():
    from sqlalchemy import select
    from app.db.models import User
    sm = get_sessionmaker()
    async with sm() as session:
        rows = (await session.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
        return {"users": [{
            "username": u.username, "display_name": u.display_name, "role": u.role,
            "active": u.active, "invited_by": u.invited_by,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        } for u in rows]}


@app.get("/api/admin/invites")
async def admin_invites():
    from sqlalchemy import select
    from app.db.models import InviteCode
    sm = get_sessionmaker()
    async with sm() as session:
        rows = (await session.execute(select(InviteCode).order_by(InviteCode.created_at.desc()).limit(500))).scalars().all()
        return {"invites": [{
            "code": v.code, "role": v.role, "note": v.note, "batch": v.batch,
            "created_by": v.created_by, "max_uses": v.max_uses, "used_count": v.used_count,
            "active": v.active,
            "expires_at": v.expires_at.isoformat() if v.expires_at else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        } for v in rows]}


@app.post("/api/admin/invites/generate")
async def admin_invites_generate(request: Request):
    import datetime as dt
    from app.db.models import InviteCode
    body = await request.json()
    data = nv_auth.generate_codes(
        count=int(body.get("count", 1)), role=str(body.get("role", "user")),
        note=str(body.get("note", "")), created_by=_admin_user(request),
        max_uses=int(body.get("max_uses", 1)),
        expires_days=int(body.get("expires_days") or 0),
    )
    base = _public_base(request)
    sm = get_sessionmaker()
    async with sm() as session:
        for code in data["codes"]:
            session.add(InviteCode(
                code=code, role=data["role"], note=data["note"], batch=data["batch"],
                created_by=data["created_by"], max_uses=data["max_uses"], expires_at=data["expires_at"],
            ))
        await session.commit()
    out = []
    for code in data["codes"]:
        url = f"{base}/register?code={code}"
        text = (
            f"NewsVerify 账号邀请\n注册地址：{url}\n邀请码：{code}\n"
            f"用法：打开链接 → 输入用户名与 4 位 PIN → 填入上方邀请码完成注册。"
            f"{('备注：' + data['note']) if data['note'] else ''}"
        )
        out.append({"code": code, "url": url, "share_text": text})
    return {"ok": True, "batch": data["batch"], "codes": out}


@app.delete("/api/admin/invites/{code}")
async def admin_invites_revoke(code: str):
    from sqlalchemy import select
    from app.db.models import InviteCode
    sm = get_sessionmaker()
    async with sm() as session:
        row = (await session.execute(select(InviteCode).where(InviteCode.code == code))).scalars().first()
        if not row:
            raise HTTPException(status_code=404, detail="invite not found")
        row.active = False
        await session.commit()
    return {"ok": True}


@app.get("/admin/api", response_class=HTMLResponse)
async def admin_api_console():
    return HTMLResponse(api_console_page(VERSION))


@app.get("/api/admin/api-keys")
async def admin_api_keys():
    from sqlalchemy import select
    from app.db.models import ApiKey
    sm = get_sessionmaker()
    async with sm() as session:
        rows = (await session.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))).scalars().all()
        return {"keys": [{
            "key": k.key, "name": k.name, "scopes": k.scopes or [], "enabled": k.enabled,
            "created_by": k.created_by, "calls": k.calls,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        } for k in rows]}


@app.post("/api/admin/api-keys")
async def admin_api_key_create(request: Request):
    import secrets
    from app.db.models import ApiKey
    body = await request.json()
    name = str(body.get("name", "")).strip()[:128] or "未命名 Key"
    scopes = body.get("scopes") or ["read"]
    if not isinstance(scopes, list):
        scopes = ["read"]
    scopes = [s for s in scopes if s in ("read", "write", "admin")] or ["read"]
    key = "nvk_" + secrets.token_urlsafe(24)
    sm = get_sessionmaker()
    async with sm() as session:
        session.add(ApiKey(key=key, name=name, scopes=scopes, enabled=True, created_by=_admin_user(request)))
        await session.commit()
    return {"ok": True, "key": key, "name": name, "scopes": scopes,
            "base_url": _public_base(request)}


@app.patch("/api/admin/api-keys/{key}")
async def admin_api_key_update(key: str, request: Request):
    from app.db.models import ApiKey
    body = await request.json()
    sm = get_sessionmaker()
    async with sm() as session:
        rec = await session.get(ApiKey, key)
        if not rec:
            raise HTTPException(status_code=404, detail="key not found")
        if "enabled" in body:
            rec.enabled = bool(body["enabled"])
        if "name" in body:
            rec.name = str(body["name"])[:128]
        if "scopes" in body and isinstance(body["scopes"], list):
            rec.scopes = [s for s in body["scopes"] if s in ("read", "write", "admin")]
        await session.commit()
    return {"ok": True}


@app.delete("/api/admin/api-keys/{key}")
async def admin_api_key_delete(key: str):
    from app.db.models import ApiKey
    sm = get_sessionmaker()
    async with sm() as session:
        rec = await session.get(ApiKey, key)
        if not rec:
            raise HTTPException(status_code=404, detail="key not found")
        await session.delete(rec)
        await session.commit()
    return {"ok": True}


@app.get("/api/admin/api/settings")
async def admin_api_settings_get():
    return {"settings": await get_api_settings(), "defaults": API_SETTING_DEFAULTS}


@app.put("/api/admin/api/settings")
async def admin_api_settings_put(request: Request):
    from app.db.models import ApiSetting
    body = await request.json()
    unknown = set(body) - set(API_SETTING_DEFAULTS)
    if unknown:
        raise HTTPException(status_code=400, detail=f"unknown setting: {', '.join(sorted(unknown))}")
    sm = get_sessionmaker()
    async with sm() as session:
        for key, value in body.items():
            rec = await session.get(ApiSetting, key)
            if rec is None:
                rec = ApiSetting(key=key)
                session.add(rec)
            rec.value = {"value": value}
            rec.updated_by = _admin_user(request)
        await session.commit()
    if "public_base_url" in body:
        app.state.public_base_url = str(body["public_base_url"] or "").strip()
    return {"ok": True, "settings": await get_api_settings()}


@app.get("/api/admin/channels")
async def admin_channels():
    return {"channels": im_registry.catalogue()}


@app.get("/admin/im", response_class=HTMLResponse)
async def admin_im_wizard():
    """Interactive, guided IM onboarding console."""
    from app.web.im_wizard import render_page
    return HTMLResponse(render_page(CHANNEL_GUIDES, public_catalogue()))


@app.get("/api/admin/channels/guide")
async def admin_channels_guide():
    """Return per-platform wizard metadata + masked saved credentials."""
    configs: dict = {}
    for key in CHANNEL_GUIDES:
        rec = await channel_store.get_record(key)
        if not rec:
            continue
        guide = CHANNEL_GUIDES[key]
        secrets = {f["name"] for f in guide.get("fields", []) if f.get("secret")}
        configs[key] = {
            "configured": bool(rec["credentials"]),
            "enabled": rec["enabled"],
            "bound_chat_id": rec["bound_chat_id"],
            "credentials": channel_store.mask_credentials(rec["credentials"], secrets),
            "last_test_ok": rec["last_test_ok"],
            "last_test_at": rec["last_test_at"],
            "last_error": rec["last_error"],
        }
    channels = []
    for c in public_catalogue():
        channels.append({**c, "configured": bool(configs.get(c["key"], {}).get("configured"))})
    return {"channels": channels, "config": configs, "guides": CHANNEL_GUIDES}


@app.post("/api/admin/channels/{key}/config")
async def admin_channel_save(key: str, request: Request):
    """Save wizard credentials. Takes effect immediately (no restart)."""
    guide = CHANNEL_GUIDES.get(key)
    if not guide:
        return JSONResponse({"error": "unknown channel"}, status_code=404)
    body = await request.json()
    old = await channel_store.get_raw_credentials(key)
    secrets = {f["name"] for f in guide.get("fields", []) if f.get("secret")}
    merged = channel_store.merge_credentials(old, body, secrets)
    await channel_store.save_record(key, merged, enabled=True)
    im_registry.set_db_credentials(key, merged)
    return {"ok": True, "configured": bool(merged), "credentials": channel_store.mask_credentials(merged, secrets)}


@app.delete("/api/admin/channels/{key}/config")
async def admin_channel_delete(key: str):
    await channel_store.delete_record(key)
    im_registry.remove_db_credentials(key)
    return {"ok": True}


@app.get("/api/admin/channels/{key}/qrcode")
async def admin_channel_qrcode(key: str):
    """Generate a binding QR (SVG) from the official deep link for this platform."""
    guide = CHANNEL_GUIDES.get(key)
    if not guide:
        return JSONResponse({"error": "unknown channel"}, status_code=404)
    creds = await channel_store.get_raw_credentials(key)
    qr = guide.get("qr", {})
    url = ""
    if qr.get("kind") == "deeplink" and qr.get("template"):
        username = (creds.get("bot_username") or "").lstrip("@")
        if not username:
            return {"error": "请先在「填写凭证」中保存机器人用户名（bot_username），再生成二维码。"}
        url = qr["template"].format(bot_username=username)
    elif qr.get("kind") == "official" and guide.get("connect_url"):
        url = guide["connect_url"]
    if not url:
        return {"error": "该平台通过官方后台扫码绑定，请打开官方配置台获取二维码。"}
    try:
        import segno
        import io
        qrcode = segno.make(url, error="m")
        buf = io.BytesIO()
        qrcode.save(buf, kind="svg", scale=5, border=2,
                    dark="#0b1220", light="#ffffff")
        svg = buf.getvalue().decode("utf-8")
        return {"ok": True, "url": url, "svg": svg}
    except Exception as e:
        return {"error": f"二维码生成失败：{e}", "url": url}


@app.get("/api/admin/channels/{key}/bind-status")
async def admin_channel_bind_status(key: str):
    """Polled by the wizard to detect that a scan-and-start completed."""
    rec = await channel_store.get_record(key)
    if not rec:
        return {"bound": False}
    return {"bound": bool(rec["bound_chat_id"]), "bound_chat_id": rec["bound_chat_id"]}


@app.post("/api/admin/channels/{key}/test")
async def admin_channel_test(key: str, request: Request):
    """Send a real test message through the configured platform adapter."""
    ch = im_registry.get(key)
    if not ch:
        return JSONResponse({"error": "unknown channel"}, status_code=404)
    try:
        body = await request.json()
    except Exception:
        body = {}
    chat = str(body.get("chat_id", "") or "")
    rec = await channel_store.get_record(key)
    if not chat and rec and rec["bound_chat_id"]:
        chat = rec["bound_chat_id"]
    if not chat:
        chat = "test"
    try:
        ok = await ch.send_message(chat, IMReply(text=str(body.get("text", "NewsVerify 接入测试消息"))))
        await channel_store.set_test_result(key, ok, "" if ok else "发送失败：请检查凭证 / Webhook 地址 / 用户 ID")
        return {"ok": ok, "configured": ch.configured, "detail": "" if ok else "请检查凭证是否正确、用户是否已与机器人建立会话"}
    except Exception as e:
        await channel_store.set_test_result(key, False, str(e)[:300])
        return {"ok": False, "configured": ch.configured, "detail": str(e)[:300]}


@app.post("/api/v1/im/{key}/webhook")
async def im_webhook(key: str, request: Request):
    """Unified inbound webhook for all instant-messaging platforms (key-authenticated)."""
    # API key is not required for inbound platform webhooks; platforms sign their
    # payloads. For generic channels the caller includes api_key query/header.
    from app.core.config import get_settings as _gs
    expected = _gs().api_key
    supplied = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if expected and supplied != expected:
        raise HTTPException(status_code=401, detail="invalid api key")
    payload = await request.json()
    signature = request.headers.get("X-Signature", "")
    # Telegram /start = scan-and-bind completion; record the chat for test pushes.
    if key == "telegram":
        msg = payload.get("message") or {}
        text = str(msg.get("text", ""))
        if text.startswith("/start"):
            cid = str((msg.get("chat") or {}).get("id", ""))
            if cid:
                try:
                    await channel_store.set_bound_chat("telegram", cid)
                except Exception:
                    pass
    reply = await im_registry.dispatch(key, payload, signature)
    return {"ok": True, "reply": reply}



@app.get("/api/status")
async def api_status():
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select, func
        from app.db.models import Job, Event, Subscription
        jobs = (await session.execute(select(func.count()).select_from(Job))).scalar() or 0
        events = (await session.execute(select(func.count()).select_from(Event))).scalar() or 0
        subs = (await session.execute(select(func.count()).select_from(Subscription).where(Subscription.active == True))).scalar() or 0
    return {"jobs": jobs, "events": events, "active_subscriptions": subs}


@app.get("/api/top-media")
async def api_top_media():
    return {"media": TOP_MEDIA, "note": NOTE}


@app.get("/api/source-policy")
async def api_source_policy():
    """可信来源白名单：只允许全球公信力靠前的媒体/核查机构/搜索引擎。"""
    from app.verification.source_policy import source_policy_payload
    return source_policy_payload()


@app.get("/api/version")
async def api_version():
    """当前版本、风格模板与更新记录（供 Web UI 展示）。"""
    payload = version_payload()
    payload["top_media_count"] = len(TOP_MEDIA)
    return payload


@app.post("/api/mindmap/share")
async def api_mindmap_share(request: Request):
    """Create an anonymous read-only snapshot of a news mind map."""
    import secrets
    from app.db.models import MindmapShare, now_utc

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)
    model = body.get("model")
    if not isinstance(model, dict) or not isinstance(model.get("root"), dict):
        return JSONResponse({"error": "missing mind-map model"}, status_code=400)
    if len(json.dumps(model, ensure_ascii=False)) > 300_000:
        return JSONResponse({"error": "mind map too large"}, status_code=400)
    token = secrets.token_urlsafe(12)
    layout = str(body.get("layout") or "tree")
    if layout not in ("tree", "waterfall", "radial"):
        layout = "tree"
    sm = get_sessionmaker()
    async with sm() as session:
        session.add(MindmapShare(token=token, event_id=str(body.get("event_id") or ""),
                                 model=model, layout=layout, created_at=now_utc()))
        await session.commit()
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme).split(",")[0].strip()
    return {"ok": True, "token": token, "url": f"{proto}://{host}/share/{token}"}


async def _get_share(token: str):
    from sqlalchemy import select
    from app.db.models import MindmapShare
    sm = get_sessionmaker()
    async with sm() as session:
        rec = (await session.execute(select(MindmapShare).where(MindmapShare.token == token))).scalar_one_or_none()
        if not rec:
            return None
        return {"model": rec.model or {}, "layout": rec.layout or "tree",
                "created_at": rec.created_at.isoformat() if rec.created_at else "",
                "event_id": rec.event_id, "views": rec.views}


@app.get("/api/mindmap/share/{token}")
async def api_mindmap_share_get(token: str):
    rec = await _get_share(token)
    if not rec:
        return JSONResponse({"error": "not found"}, status_code=404)
    return rec


@app.get("/api/mindmap/share/{token}/qrcode")
async def api_mindmap_share_qr(token: str, request: Request):
    rec = await _get_share(token)
    if not rec:
        return JSONResponse({"error": "not found"}, status_code=404)
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme).split(",")[0].strip()
    url = f"{proto}://{host}/share/{token}"
    try:
        import io
        import segno
        qr = segno.make(url, error="m")
        buf = io.BytesIO()
        qr.save(buf, kind="svg", scale=5, border=2, dark="#0b1220", light="#ffffff")
        return HTMLResponse(buf.getvalue().decode("utf-8"), media_type="image/svg+xml")
    except Exception as exc:
        return JSONResponse({"error": f"QR 生成失败：{exc}"}, status_code=500)


@app.delete("/api/mindmap/share/{token}")
async def api_mindmap_share_delete(token: str):
    from sqlalchemy import delete
    from app.db.models import MindmapShare
    sm = get_sessionmaker()
    async with sm() as session:
        result = await session.execute(delete(MindmapShare).where(MindmapShare.token == token))
        await session.commit()
    return {"ok": result.rowcount > 0}


@app.get("/share/{token}", response_class=HTMLResponse)
async def mindmap_share_page(token: str):
    from sqlalchemy import select
    from app.db.models import MindmapShare
    rec = await _get_share(token)
    if not rec:
        return HTMLResponse("<h1 style='font-family:sans-serif;padding:40px'>脑图分享链接不存在或已撤销</h1>",
                            status_code=404)
    sm = get_sessionmaker()
    async with sm() as session:
        row = (await session.execute(select(MindmapShare).where(MindmapShare.token == token))).scalar_one_or_none()
        if row:
            row.views = (row.views or 0) + 1
            await session.commit()
    return HTMLResponse(mm_share_page(rec, token, rec["created_at"]))


@app.get("/api/events")
async def api_events():
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select, func
        from app.db.models import Event, Job, Verdict, Claim, Subscription
        res = await session.execute(select(Event).order_by(Event.created_at.desc()).limit(50))
        events = res.scalars().all()
        out = []
        for e in events:
            jobs_res = await session.execute(select(Job).where(Job.payload["event_id"].as_string() == e.id).order_by(Job.created_at.desc()).limit(1))
            job = jobs_res.scalars().first()
            verdicts_res = await session.execute(select(Verdict).where(Verdict.event_id == e.id))
            vs = verdicts_res.scalars().all()
            claims_res = await session.execute(select(Claim).where(Claim.event_id == e.id))
            cs = claims_res.scalars().all()
            # 活跃订阅数：用于列表卡片正确点亮“持续追踪”节点（过去前端写死 0）
            sub_res = await session.execute(
                select(func.count()).select_from(Subscription).where(
                    Subscription.event_id == e.id, Subscription.active == True  # noqa: E712
                )
            )
            active_subs = sub_res.scalar() or 0
            # 列表只需轻量 job_result：summary / progress / 媒体覆盖汇总，
            # 不返回庞大的 top_media 明细（详情接口按需返回）。
            slim_result = None
            if job and job.result:
                jr = job.result
                slim_result = {
                    "summary": jr.get("summary"),
                    "progress": jr.get("progress"),
                    "top_media": bool(jr.get("top_media")),
                    "media_hits": jr.get("media_hits") or 0,
                    "total_reports": jr.get("total_reports") or 0,
                }
            out.append({
                "id": e.id,
                "title": e.title,
                "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "job_id": job.id if job else None,
                "job_status": job.status if job else None,
                "job_result": slim_result,
                "active_subs": active_subs,
                "claims": [{"id": c.id, "text": c.text, "language": c.language} for c in cs],
                "verdicts": [{"label": v.label, "confidence": v.confidence, "rationale": v.rationale,
                              "counter_argument": v.counter_argument, "evidence_gaps": v.evidence_gaps} for v in vs],
            })
        return out


@app.get("/api/events/{event_id}")
async def api_event_detail(event_id: str):
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select
        from app.db.models import Event, Job, Verdict, Claim, Evidence, Source, Subscription
        e = await session.get(Event, event_id)
        if not e:
            return JSONResponse({"error": "not found"}, status_code=404)
        jobs_res = await session.execute(select(Job).where(Job.payload["event_id"].as_string() == event_id).order_by(Job.created_at.desc()))
        jobs = jobs_res.scalars().all()
        claims_res = await session.execute(select(Claim).where(Claim.event_id == event_id))
        claims = claims_res.scalars().all()
        verdicts_res = await session.execute(select(Verdict).where(Verdict.event_id == event_id))
        verdicts = verdicts_res.scalars().all()
        claim_details = []
        for c in claims:
            ev_res = await session.execute(select(Evidence).where(Evidence.claim_id == c.id))
            evs = ev_res.scalars().all()
            ev_list = []
            for evi in evs:
                src = await session.get(Source, evi.source_id)
                src_url = src.url if src else ""
                stype, _ = classify_source(src_url)
                # 反查该来源属于 Top30 的哪家、名次、事实等级；并取报道/抓取时间
                rank = None; media_name = None; factual = None
                dom = (src.domain if src else "") or ""
                for m in TOP_MEDIA:
                    md = m["domain"]
                    if dom == md or dom.endswith("." + md) or md in src_url:
                        rank = m["rank"]; media_name = m["name"]; factual = m.get("factual")
                        break
                reported_at = None
                if src:
                    reported_at = (getattr(src, "published_at", None) or getattr(src, "fetched_at", None) or getattr(src, "created_at", None))
                    reported_at = reported_at.isoformat() if reported_at else None
                ev_list.append({"snippet": evi.snippet, "stance": evi.stance, "url": src_url,
                                "domain": dom, "title": src.title if src else "",
                                "source_type": stype or "untrusted",
                                "media_rank": rank, "media_name": media_name, "factual": factual,
                                "reported_at": reported_at})
            v = next((x for x in verdicts if x.claim_id == c.id), None)
            claim_details.append({
                "id": c.id, "text": c.text, "language": c.language,
                "verdict": {"label": v.label, "confidence": v.confidence, "rationale": v.rationale,
                            "counter_argument": v.counter_argument, "evidence_gaps": v.evidence_gaps} if v else None,
                "evidence": ev_list,
            })
        subs_res = await session.execute(select(Subscription).where(Subscription.event_id == event_id))
        subs = subs_res.scalars().all()
        # 追踪更新通知（用于“汇总所有更新状态”）
        notif_list = []
        if subs:
            from app.db.models import Notification
            sub_ids = [s.id for s in subs]
            nres = await session.execute(
                select(Notification).where(Notification.subscription_id.in_(sub_ids)).order_by(Notification.sent_at.desc())
            )
            for n in nres.scalars().all():
                notif_list.append({
                    "id": n.id, "kind": n.kind, "content_hash": n.content_hash,
                    "created_at": n.sent_at.isoformat() if n.sent_at else None,
                })
        top_media = None
        summary = None
        top_media_by_claim = []
        media_hits = 0
        total_reports = 0
        if jobs:
            jr = jobs[0].result or {}
            top_media = jr.get("top_media")
            summary = jr.get("summary")
            top_media_by_claim = jr.get("top_media_by_claim") or []
            media_hits = jr.get("media_hits") or 0
            total_reports = jr.get("total_reports") or 0
        return {
            "id": e.id, "title": e.title, "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "jobs": [{"id": j.id, "kind": j.kind, "status": j.status, "result": j.result, "error": j.error,
                      "attempts": j.attempts,
                      "started_at": j.started_at.isoformat() if j.started_at else None,
                      "finished_at": j.finished_at.isoformat() if j.finished_at else None} for j in jobs],
            "claims": claim_details,
            "subscriptions": [{
                "id": s.id, "active": s.active, "paused": s.paused,
                "interval_hours": s.interval_hours,
                "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
                "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
            } for s in subs],
            "notifications": notif_list,
            "top_media": top_media,
            "top_media_by_claim": top_media_by_claim,
            "media_hits": media_hits,
            "total_reports": total_reports,
            "summary": summary,
        }


@app.put("/api/events/{event_id}")
async def api_update_event(event_id: str, request: Request):
    body = await request.json()
    title = body.get("title")
    sm = get_sessionmaker()
    async with sm() as session:
        from app.db.models import Event
        e = await session.get(Event, event_id)
        if not e:
            return JSONResponse({"error": "not found"}, status_code=404)
        if title is not None:
            e.title = str(title)[:500]
        await session.commit()
        return {"ok": True, "title": e.title}


def _interval_to_hours(interval: str) -> int:
    mapping = {"6h": 6, "24h": 24, "week": 168, "12h": 12, "3d": 72}
    return mapping.get(interval, 24)


@app.post("/api/track/{event_id}")
async def api_track(event_id: str, interval: str = "24h"):
    """开启或更新追踪。已有活跃订阅时更新其间隔，避免重复创建。"""
    sm = get_sessionmaker()
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select
    from app.db.models import Subscription
    iv = _interval_to_hours(interval)
    async with sm() as session:
        res = await session.execute(
            select(Subscription).where(Subscription.event_id == event_id, Subscription.active == True)
        )
        sub = res.scalars().first()
        if sub:
            sub.interval_hours = iv
            sub.paused = False
            sub.active = True
            sub.next_run_at = datetime.now(timezone.utc) + timedelta(hours=iv)
        else:
            sub = Subscription(event_id=event_id, user_id=0, chat_id=0, interval_hours=iv,
                               next_run_at=datetime.now(timezone.utc) + timedelta(hours=iv))
            session.add(sub)
        await session.commit()
        return {"subscription_id": sub.id, "interval_hours": iv,
                "next_run_at": sub.next_run_at.isoformat() if sub.next_run_at else None}


@app.post("/api/track/{event_id}/settings")
async def api_track_settings(event_id: str, request: Request):
    """独立设置：修改追踪间隔/暂停状态/下次时间等约定并更新逻辑。"""
    body = await request.json()
    sm = get_sessionmaker()
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import select
    from app.db.models import Subscription
    async with sm() as session:
        res = await session.execute(
            select(Subscription).where(Subscription.event_id == event_id, Subscription.active == True)
        )
        sub = res.scalars().first()
        if not sub:
            return JSONResponse({"error": "no active subscription"}, status_code=404)
        if "interval" in body or "interval_hours" in body:
            raw = body.get("interval_hours") or body.get("interval")
            iv = _interval_to_hours(raw) if isinstance(raw, str) else int(raw)
            sub.interval_hours = iv
            sub.next_run_at = datetime.now(timezone.utc) + timedelta(hours=iv)
        if "paused" in body:
            sub.paused = bool(body["paused"])
        if "next_run_at" in body and body["next_run_at"]:
            try:
                sub.next_run_at = datetime.fromisoformat(str(body["next_run_at"]).replace("Z", "+00:00"))
            except Exception:
                pass
        await session.commit()
        return {
            "ok": True, "interval_hours": sub.interval_hours, "paused": sub.paused,
            "next_run_at": sub.next_run_at.isoformat() if sub.next_run_at else None,
        }


@app.post("/api/untrack/{event_id}")
async def api_untrack(event_id: str):
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import update
        from app.db.models import Subscription
        await session.execute(update(Subscription).where(Subscription.event_id == event_id).values(active=False, paused=True))
        await session.commit()
        return {"ok": True}


@app.delete("/api/events/{event_id}")
async def api_delete_event(event_id: str):
    sm = get_sessionmaker()
    async with sm() as session:
        from app.db.models import Event
        e = await session.get(Event, event_id)
        if not e:
            return JSONResponse({"error": "not found"}, status_code=404)
        await session.delete(e)
        await session.commit()
        return {"ok": True}


@app.post("/api/recheck/{event_id}")
async def api_recheck(event_id: str):
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select
        from app.db.models import Event, Job
        e = await session.get(Event, event_id)
        if not e:
            return JSONResponse({"error": "not found"}, status_code=404)
        # 优先取最近一次 job 里的完整原文；Event.title 只是截断到 120 字的展示标题，
        # 用它重查会丢失原文导致主张拆分质量下降。
        prev = await session.execute(
            select(Job).where(Job.payload["event_id"].as_string() == e.id).order_by(Job.created_at.desc()).limit(1)
        )
        prev_job = prev.scalars().first()
        raw_text = (prev_job.payload or {}).get("text") if prev_job else None
        full_text = raw_text or e.title
        job = Job(kind="check", status="queued",
                  payload={"event_id": e.id, "text": full_text, "urls": [], "deep": False,
                           "chat_id": None, "user_id": None,
                           "mode": (prev_job.payload or {}).get("mode", "full") if prev_job else "full",
                           "freq": "none"}, user_id=None, chat_id=None)
        session.add(job)
        e.status = "queued"
        await session.commit()
        return {"job_id": job.id}


# ---------- Public API v1 (key-authenticated) ----------
@app.get("/api/v1/status")
async def api_v1_status(ok: bool = Depends(verify_api_key)):
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select, func
        from app.db.models import Job, Event, Subscription
        jobs = (await session.execute(select(func.count()).select_from(Job))).scalar() or 0
        events = (await session.execute(select(func.count()).select_from(Event))).scalar() or 0
        subs = (await session.execute(select(func.count()).select_from(Subscription).where(Subscription.active == True))).scalar() or 0
    return {"jobs": jobs, "events": events, "active_subscriptions": subs, "version": VERSION}


@app.get("/api/v1/version")
async def api_v1_version(ok: bool = Depends(verify_api_key)):
    payload = version_payload()
    payload["top_media_count"] = len(TOP_MEDIA)
    return payload


@app.get("/api/v1/top-media")
async def api_v1_top_media(ok: bool = Depends(verify_api_key)):
    return {"media": TOP_MEDIA, "note": NOTE}


@app.get("/api/v1/source-policy")
async def api_v1_source_policy(ok: bool = Depends(verify_api_key)):
    from app.verification.source_policy import source_policy_payload
    return source_policy_payload()


@app.get("/api/v1/keys/me")
async def api_v1_key_info(request: Request, ok: bool = Depends(verify_api_key)):
    info = getattr(request.state, "api_key", {}) or {}
    return {"name": info.get("name", ""), "scopes": info.get("scopes", []),
            "key_prefix": str(info.get("key", ""))[:8] + "…", "version": VERSION}


@app.get("/api/v1/query/news")
async def api_v1_query_news(q: str = "", status: str = "", limit: int = 20,
                            ok: bool = Depends(verify_api_key)):
    """Search verification events by title; returns compact cards with verdicts."""
    from sqlalchemy import select, or_
    from app.db.models import Event, Job, Verdict
    cap = int((await get_api_settings()).get("max_results", 100))
    limit = max(1, min(limit, cap))
    sm = get_sessionmaker()
    async with sm() as session:
        stmt = select(Event)
        if q:
            like = f"%{q.strip()}%"
            stmt = stmt.where(or_(Event.title.ilike(like), Event.id.ilike(like)))
        if status:
            stmt = stmt.where(Event.status == status)
        rows = (await session.execute(stmt.order_by(Event.created_at.desc()).limit(limit))).scalars().all()
        out = []
        for e in rows:
            job = (await session.execute(
                select(Job).where(Job.payload["event_id"].as_string() == e.id).order_by(Job.created_at.desc()).limit(1)
            )).scalars().first()
            verdicts = (await session.execute(select(Verdict).where(Verdict.event_id == e.id))).scalars().all()
            out.append({
                "event_id": e.id, "title": e.title, "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "job_status": job.status if job else None,
                "verdicts": [{"label": v.label, "confidence": v.confidence} for v in verdicts],
            })
        return {"query": q, "status": status, "count": len(out), "limit": limit, "results": out}


@app.get("/api/v1/events/{event_id}/process")
async def api_v1_event_process(event_id: str, ok: bool = Depends(verify_api_key)):
    """Every process artifact for one event: jobs, progress, claims, verdicts,
    evidence with source metadata, subscription state, notifications and media."""
    sm = get_sessionmaker()
    async with sm() as session:
        payload = await build_process(session, event_id)
    if not payload:
        raise HTTPException(status_code=404, detail="event not found")
    return payload


@app.get("/api/v1/events/{event_id}/mindmap")
async def api_v1_event_mindmap(event_id: str, layout: str = "tree",
                               ok: bool = Depends(verify_api_key)):
    sm = get_sessionmaker()
    async with sm() as session:
        payload = await build_process(session, event_id)
    if not payload:
        raise HTTPException(status_code=404, detail="event not found")
    return {"event_id": event_id, "layout": layout if layout in ("tree", "waterfall", "radial") else "tree",
            "model": payload["mindmap"], "share_hint": "POST /api/mindmap/share with this model"}


@app.get("/api/v1/jobs/{job_id}")
async def api_v1_job(job_id: str, ok: bool = Depends(verify_api_key)):
    from app.db.models import Job
    sm = get_sessionmaker()
    async with sm() as session:
        job = await session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return {
            "id": job.id, "kind": job.kind, "status": job.status, "attempts": job.attempts,
            "error": job.error, "result": job.result, "payload": job.payload,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        }


@app.post("/api/v1/check")
async def api_v1_check(request: Request, ok: bool = Depends(verify_api_key)):
    body = await request.json()
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text required")
    mode = body.get("mode", "full")
    freq = body.get("freq", "none")
    sm = get_sessionmaker()
    async with sm() as session:
        from app.db.models import Event, Job
        ev = Event(title=text[:120] or "news", status="queued")
        session.add(ev)
        await session.flush()
        job = Job(kind="check", status="queued", payload={"event_id": ev.id, "text": text, "urls": [], "deep": False, "chat_id": None, "user_id": None, "mode": mode, "freq": freq}, user_id=None, chat_id=None)
        session.add(job)
        await session.commit()
        return {"event_id": ev.id, "job_id": job.id, "status": "queued"}


@app.get("/api/v1/events")
async def api_v1_events(ok: bool = Depends(verify_api_key)):
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select
        from app.db.models import Event, Job, Verdict, Claim
        res = await session.execute(select(Event).order_by(Event.created_at.desc()).limit(50))
        events = res.scalars().all()
        out = []
        for e in events:
            jobs_res = await session.execute(select(Job).where(Job.payload["event_id"].as_string() == e.id).order_by(Job.created_at.desc()).limit(1))
            job = jobs_res.scalars().first()
            verdicts_res = await session.execute(select(Verdict).where(Verdict.event_id == e.id))
            vs = verdicts_res.scalars().all()
            claims_res = await session.execute(select(Claim).where(Claim.event_id == e.id))
            cs = claims_res.scalars().all()
            out.append({
                "id": e.id, "title": e.title, "status": e.status,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "job_id": job.id if job else None, "job_status": job.status if job else None,
                "job_result": job.result if job else None,
                "claims": [{"id": c.id, "text": c.text, "language": c.language} for c in cs],
                "verdicts": [{"label": v.label, "confidence": v.confidence, "rationale": v.rationale,
                              "counter_argument": v.counter_argument, "evidence_gaps": v.evidence_gaps} for v in vs],
            })
        return out


@app.get("/api/v1/events/{event_id}")
async def api_v1_event_detail(event_id: str, ok: bool = Depends(verify_api_key)):
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select
        from app.db.models import Event, Job, Verdict, Claim, Evidence, Source, Subscription
        e = await session.get(Event, event_id)
        if not e:
            raise HTTPException(status_code=404, detail="not found")
        jobs_res = await session.execute(select(Job).where(Job.payload["event_id"].as_string() == event_id).order_by(Job.created_at.desc()))
        jobs = jobs_res.scalars().all()
        claims_res = await session.execute(select(Claim).where(Claim.event_id == event_id))
        claims = claims_res.scalars().all()
        verdicts_res = await session.execute(select(Verdict).where(Verdict.event_id == event_id))
        verdicts = verdicts_res.scalars().all()
        claim_details = []
        for c in claims:
            ev_res = await session.execute(select(Evidence).where(Evidence.claim_id == c.id))
            evs = ev_res.scalars().all()
            ev_list = []
            for evi in evs:
                src = await session.get(Source, evi.source_id)
                src_url = src.url if src else ""
                stype, _ = classify_source(src_url)
                # 反查该来源属于 Top30 的哪家、名次、事实等级；并取报道/抓取时间
                rank = None; media_name = None; factual = None
                dom = (src.domain if src else "") or ""
                for m in TOP_MEDIA:
                    md = m["domain"]
                    if dom == md or dom.endswith("." + md) or md in src_url:
                        rank = m["rank"]; media_name = m["name"]; factual = m.get("factual")
                        break
                reported_at = None
                if src:
                    reported_at = (getattr(src, "published_at", None) or getattr(src, "fetched_at", None) or getattr(src, "created_at", None))
                    reported_at = reported_at.isoformat() if reported_at else None
                ev_list.append({"snippet": evi.snippet, "stance": evi.stance, "url": src_url,
                                "domain": dom, "title": src.title if src else "",
                                "source_type": stype or "untrusted",
                                "media_rank": rank, "media_name": media_name, "factual": factual,
                                "reported_at": reported_at})
            v = next((x for x in verdicts if x.claim_id == c.id), None)
            claim_details.append({
                "id": c.id, "text": c.text, "language": c.language,
                "verdict": {"label": v.label, "confidence": v.confidence, "rationale": v.rationale,
                            "counter_argument": v.counter_argument, "evidence_gaps": v.evidence_gaps} if v else None,
                "evidence": ev_list,
            })
        subs_res = await session.execute(select(Subscription).where(Subscription.event_id == event_id))
        subs = subs_res.scalars().all()
        top_media = None
        summary = None
        if jobs:
            top_media = (jobs[0].result or {}).get("top_media") if jobs[0].result else None
            summary = (jobs[0].result or {}).get("summary") if jobs[0].result else None
        return {
            "id": e.id, "title": e.title, "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "jobs": [{"id": j.id, "kind": j.kind, "status": j.status, "result": j.result, "error": j.error,
                      "attempts": j.attempts,
                      "started_at": j.started_at.isoformat() if j.started_at else None,
                      "finished_at": j.finished_at.isoformat() if j.finished_at else None} for j in jobs],
            "claims": claim_details,
            "subscriptions": [{"id": s.id, "active": s.active, "interval_hours": s.interval_hours} for s in subs],
            "top_media": top_media, "summary": summary,
        }


@app.post("/api/v1/track/{event_id}")
async def api_v1_track(event_id: str, request: Request, ok: bool = Depends(verify_api_key)):
    body = await request.json() if request.headers.get("content-type","").startswith("application/json") else {}
    interval = (body or {}).get("interval", "24h")
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select
        from app.db.models import Subscription
        from datetime import datetime, timezone, timedelta
        iv = _interval_to_hours(interval)
        # 幂等：已有活跃订阅则更新，避免重复调用产生多条追踪任务。
        res = await session.execute(
            select(Subscription).where(Subscription.event_id == event_id, Subscription.active == True)  # noqa: E712
        )
        sub = res.scalars().first()
        if sub:
            sub.interval_hours = iv
            sub.paused = False
            sub.active = True
            sub.next_run_at = datetime.now(timezone.utc) + timedelta(hours=iv)
        else:
            sub = Subscription(event_id=event_id, user_id=0, chat_id=0, interval_hours=iv,
                               next_run_at=datetime.now(timezone.utc) + timedelta(hours=iv))
            session.add(sub)
        await session.commit()
        return {"subscription_id": sub.id, "interval_hours": iv}


@app.post("/api/v1/untrack/{event_id}")
async def api_v1_untrack(event_id: str, ok: bool = Depends(verify_api_key)):
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import update
        from app.db.models import Subscription
        await session.execute(update(Subscription).where(Subscription.event_id == event_id).values(active=False, paused=True))
        await session.commit()
        return {"ok": True}


@app.delete("/api/v1/events/{event_id}")
async def api_v1_delete(event_id: str, ok: bool = Depends(verify_api_key)):
    sm = get_sessionmaker()
    async with sm() as session:
        from app.db.models import Event
        e = await session.get(Event, event_id)
        if not e:
            raise HTTPException(status_code=404, detail="not found")
        await session.delete(e)
        await session.commit()
        return {"ok": True}


@app.post("/submit")
async def submit(text: str = Form(...), mode: str = Form("full"), freq: str = Form("none")):
    sm = get_sessionmaker()
    async with sm() as session:
        from app.db.models import Event, Job
        ev = Event(title=text[:120] or "news", status="queued")
        session.add(ev)
        await session.flush()
        job = Job(kind="check", status="queued", payload={"event_id": ev.id, "text": text, "urls": [], "deep": False, "chat_id": None, "user_id": None, "mode": mode, "freq": freq}, user_id=None, chat_id=None)
        session.add(job)
        await session.commit()
        return JSONResponse({"event_id": ev.id, "job_id": job.id})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request = None):
    session = nv_auth.parse_session(request.cookies.get("nv_auth")) if request else None
    username = (session or {}).get("username", "admin")
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NewsVerify 新闻事实核查控制台</title>
<style>
__THEME_CSS__
__DESIGN_CSS__
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;background:radial-gradient(1200px 600px at 10% -10%,var(--hero-a) 0%,transparent 60%),radial-gradient(1000px 500px at 90% 0%,var(--hero-b) 0%,transparent 60%),var(--bg);color:var(--text);min-height:100vh}
.wrap{max-width:1440px;margin:0 auto;padding:24px}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;flex-wrap:wrap;gap:12px}
.brand{display:flex;align-items:center;gap:12px}
.logo{width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;font-weight:800;color:var(--on-accent);font-size:18px;box-shadow:var(--shadow)}
h1{font-size:24px;font-weight:700}
.sub{color:var(--muted);font-size:12px;margin-top:2px}
.badge{display:inline-block;padding:4px 12px;border-radius:999px;font-size:11px;background:rgba(56,189,248,.12);color:var(--accent);border:1px solid rgba(56,189,248,.3)}

/* ==== v0.5.x 顶部导航 / 主题模板 ==== */
.topbar{align-items:flex-start}
.brand .kicker{font-size:10px;letter-spacing:2.2px;color:var(--accent);font-weight:800;margin-bottom:5px}
.header-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.theme-switch{display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--surface-1);color:var(--muted);font-size:11px}
.theme-switch select{background:var(--surface-0);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:5px 8px;font-size:12px;outline:none}
.version-btn{display:flex;align-items:center;gap:7px;padding:8px 13px;border-radius:999px;border:1px solid var(--border);background:var(--surface-1);color:var(--text);font-size:12px;font-weight:700;cursor:pointer;transition:all .15s}
.version-btn:hover{border-color:var(--accent);color:var(--accent)}
.v-dot{width:7px;height:7px;border-radius:50%;background:var(--ok);box-shadow:0 0 9px var(--ok)}
/* 背景音乐控件 */
.music-btn{display:flex;align-items:center;gap:6px;padding:8px 12px;border-radius:999px;border:1px solid var(--border);background:var(--surface-1);color:var(--text);font-size:12px;cursor:pointer;transition:all .15s}
.music-btn:hover{border-color:var(--accent);color:var(--accent)}
.music-btn.playing{border-color:var(--accent3);color:var(--ok-text)}
.music-note{font-size:13px}
.music-panel{position:fixed;right:20px;bottom:20px;z-index:55;background:var(--card);border:1px solid var(--border);border-radius:16px;padding:16px;box-shadow:var(--shadow);width:min(360px,92vw);display:none;opacity:0;transform:translateY(14px);transition:opacity .32s ease,transform .32s ease}
.music-panel.show{opacity:1;transform:translateY(0)}
.music-panel.hide{opacity:0;transform:translateY(14px);pointer-events:none}
.music-panel h3{font-size:14px;color:var(--accent);margin-bottom:4px;display:flex;align-items:center;justify-content:space-between;gap:10px}
.music-close{border:1px solid var(--border);background:var(--surface-1);color:var(--muted);border-radius:8px;width:26px;height:26px;line-height:1;cursor:pointer;font-size:16px;transition:all .15s}
.music-close:hover{color:var(--danger);border-color:var(--danger)}
.music-list{max-height:min(54vh,430px);overflow-y:auto;overflow-x:hidden;padding-right:6px;scrollbar-width:thin;scrollbar-color:var(--accent) var(--surface-2)}
.music-track{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:9px 11px;border-radius:10px;border:1px solid var(--border);background:var(--surface-0);margin-top:7px;cursor:pointer;font-size:12px;transition:all .15s}
.music-track:hover{border-color:var(--accent)}
.music-track.active{border-color:var(--accent3);background:var(--reported-bg)}
.music-track .mt-title{font-weight:700;color:var(--text)}
.music-track .mt-desc{font-size:10px;color:var(--muted);margin-top:2px}
.music-track .mt-icon{font-size:16px}
.music-row{display:flex;align-items:center;gap:10px;margin-top:12px;font-size:11px;color:var(--muted);border-top:1px solid var(--border);padding-top:10px}
.music-row input[type=range]{flex:1;accent-color:var(--accent)}
.nav{display:flex;gap:6px;flex-wrap:wrap;margin:-6px 0 18px;padding:6px;border:1px solid var(--border);border-radius:var(--radius);background:var(--surface-1);box-shadow:var(--shadow)}
.nav a{color:var(--muted);text-decoration:none;font-size:12px;padding:6px 12px;border-radius:8px;transition:all .15s}
.nav a:hover{background:var(--surface-2);color:var(--accent)}
.section-anchor{scroll-margin-top:18px}
.footer{margin-top:24px;padding:18px 4px 8px;border-top:1px solid var(--border);display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;color:var(--muted);font-size:11px}
.footer-links{display:flex;gap:14px;flex-wrap:wrap}
.footer a{color:var(--accent);text-decoration:none}
.footer a:hover{text-decoration:underline}
.release-item{background:var(--surface-0);border:1px solid var(--border);border-radius:10px;padding:12px;margin:8px 0}
.release-head{display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap}
.release-head b{color:var(--accent)}
.release-item ul{margin:8px 0 0 18px;color:var(--muted);font-size:12px;line-height:1.7}
.theme-sample{display:flex;gap:6px;margin-top:6px}
.theme-sample i{width:14px;height:14px;border-radius:4px;display:inline-block;border:1px solid var(--border)}

.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px}
@media(max-width:900px){.stats{grid-template-columns:repeat(2,1fr)}}
.card{background:linear-gradient(180deg,var(--card),var(--card2));border:1px solid var(--border);border-radius:16px;padding:18px;box-shadow:var(--shadow)}
.stat .n{font-size:34px;font-weight:800;background:linear-gradient(90deg,var(--accent),var(--accent3));-webkit-background-clip:text;background-clip:text;color:transparent}
.stat .l{color:var(--muted);font-size:12px;margin-top:4px}

.layout{display:grid;grid-template-columns:1fr 360px;gap:18px;margin-bottom:18px}
@media(max-width:1100px){.layout{grid-template-columns:1fr}}

.panel{background:linear-gradient(180deg,var(--card),var(--card2));border:1px solid var(--border);border-radius:16px;padding:18px;box-shadow:var(--shadow)}
.panel h2{font-size:16px;margin-bottom:12px;color:var(--accent);display:flex;align-items:center;gap:8px;font-weight:700}
.panel h2 .icon{width:22px;height:22px;border-radius:6px;background:rgba(56,189,248,.15);display:inline-flex;align-items:center;justify-content:center;font-size:12px}

/* submit */
textarea{width:100%;min-height:100px;background:var(--surface-0);color:var(--text);border:1px solid var(--border);border-radius:12px;padding:12px;font-size:14px;resize:vertical;font-family:inherit;line-height:1.6}
textarea:focus{outline:none;border-color:var(--accent)}
.btn{background:linear-gradient(90deg,var(--accent),var(--accent2));color:var(--on-accent);border:none;border-radius:12px;padding:10px 20px;font-weight:700;cursor:pointer;font-size:14px;transition:transform .15s,opacity .15s}
.btn:hover{opacity:.92;transform:translateY(-1px)}
.btn.secondary{background:var(--card2);color:var(--text);border:1px solid var(--border)}
.btn.ghost{background:transparent;border:1px solid var(--border);color:var(--muted)}
.btn.small{padding:6px 12px;font-size:12px}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}

/* top media：固定高度 + 常驻滚动条，一屏内可滚动查看全部 30 家 */
.media-list{display:flex;flex-direction:column;gap:8px;height:560px;overflow-y:auto;overflow-x:hidden;padding-right:8px;scrollbar-width:thin;scrollbar-color:var(--accent) var(--surface-2)}
.media-list::-webkit-scrollbar{width:8px}
.media-list::-webkit-scrollbar-track{background:var(--surface-2);border-radius:8px}
.media-list::-webkit-scrollbar-thumb{background:linear-gradient(180deg,var(--accent),var(--accent2));border-radius:8px}
.media-list::-webkit-scrollbar-thumb:hover{background:var(--accent-soft)}
.media-scroll-hint{font-size:10px;color:var(--muted);margin-bottom:6px;display:flex;align-items:center;gap:5px}
.media-scroll-hint .sc-line{display:inline-block;width:26px;height:4px;border-radius:4px;background:linear-gradient(90deg,var(--accent),var(--accent2))}
.media-item{background:var(--surface-0);border:1px solid var(--border);border-radius:12px;padding:12px;transition:border-color .15s}
.media-item:hover{border-color:var(--accent)}
.media-item .head{display:flex;justify-content:space-between;align-items:center;gap:8px}
.media-item .name{font-weight:700;font-size:13px;color:var(--accent)}
.media-item .rank{font-size:11px;color:var(--muted)}
.media-item a{color:var(--accent);text-decoration:none;font-size:12px}
.media-item a:hover{text-decoration:underline}
.media-item .why{color:var(--muted);margin-top:6px;font-size:11px;line-height:1.55}
.media-item .status{font-size:11px;margin-top:6px;padding:4px 8px;border-radius:6px;background:var(--surface-2);display:inline-block}

/* ==== 媒体报道状态：点亮 / 灰色 ==== */
.ml-dot{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:8px;vertical-align:middle;background:var(--surface-2);border:1px solid var(--border);box-shadow:none;transition:all .2s}
.ml-dot.lit{background:var(--ok);border-color:var(--ok);box-shadow:0 0 10px rgba(34,197,94,.8)}
.media-item.reported{border-color:rgba(34,197,94,.45);background:var(--reported-bg)}
.media-item.reported .name{color:var(--ok-text)}
.media-item .status.hit{background:rgba(34,197,94,.15);color:var(--ok-text)}
.media-item .status.miss{background:var(--surface-2);color:var(--muted)}
.media-cover{display:flex;align-items:center;gap:6px;margin-top:6px;font-size:11px;color:var(--muted)}
.media-cover b{color:var(--ok-text);font-variant-numeric:tabular-nums}
.src-link{display:block;color:var(--accent);text-decoration:none;font-size:11px;padding:3px 0;border-bottom:1px dashed var(--border)}
.src-link:hover{text-decoration:underline;color:var(--accent-soft)}
.src-list{margin-top:4px;max-height:150px;overflow:auto}

/* ==== 任务卡片双操作按钮 ==== */
.card-actions{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.mini-btn{font-size:11px;padding:5px 10px;border-radius:8px;border:1px solid var(--border);background:var(--surface-2);color:var(--text);cursor:pointer;transition:all .15s}
.mini-btn:hover{border-color:var(--accent);color:var(--accent)}
.mini-btn.track{border-color:rgba(34,197,94,.35);color:var(--ok-text)}
.mini-btn.setting{border-color:rgba(129,140,248,.35);color:var(--accent2-soft)}

/* ==== 追踪状态汇总 ==== */
.track-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0}
@media(max-width:600px){.track-grid{grid-template-columns:1fr}}
.track-stat{background:var(--surface-0);border:1px solid var(--border);border-radius:10px;padding:10px;text-align:center}
.track-stat .v{font-size:20px;font-weight:800;color:var(--accent)}
.track-stat .l{font-size:11px;color:var(--muted);margin-top:3px}
.upd-item{background:var(--surface-0);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12px;margin:5px 0}
.upd-item .u-time{color:var(--muted);font-size:11px}
.setting-row{display:flex;align-items:center;gap:8px;margin:8px 0;font-size:12px}
.setting-row label{color:var(--muted);min-width:96px}
.setting-row select,.setting-row input[type=datetime-local]{background:var(--surface-0);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:6px 10px;font-size:12px}

/* history */
.tabs{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.tab{padding:6px 14px;border-radius:8px;background:var(--surface-2);color:var(--muted);cursor:pointer;font-size:12px;border:1px solid var(--border);transition:all .15s}
.tab.active{background:var(--accent);color:var(--on-accent);border-color:var(--accent);font-weight:700}
.hist{max-height:520px;overflow:auto}
.hitem{padding:14px;border-bottom:1px solid var(--border);cursor:pointer;transition:background .15s}
.hitem:hover{background:var(--surface-2)}
.hitem .top{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}
.hitem .title{font-size:14px;font-weight:600;flex:1;line-height:1.5}
.hitem .meta{color:var(--muted);font-size:11px;margin-top:6px;display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.tag{display:inline-block;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:.3px}
.tag.supported{background:rgba(34,197,94,.15);color:var(--ok-text)}
.tag.refuted{background:rgba(239,68,68,.15);color:var(--bad-text)}
.tag.mixed{background:rgba(245,158,11,.15);color:var(--warn-text)}
.tag.insufficient_evidence{background:rgba(148,163,184,.12);color:var(--muted)}
.tag.outdated{background:rgba(129,140,248,.15);color:var(--accent2-soft)}
.tag.not_checkable{background:rgba(107,114,128,.2);color:var(--muted)}
.tag.queued,.tag.running{background:rgba(56,189,248,.15);color:var(--accent-soft)}
.tag.done{background:rgba(34,197,94,.15);color:var(--ok-text)}
.tag.failed{background:rgba(239,68,68,.15);color:var(--bad-text)}

/* modal */
.modal-bg{position:fixed;inset:0;background:rgba(4,8,20,.75);backdrop-filter:blur(4px);display:none;align-items:center;justify-content:center;z-index:60;padding:20px}
.modal{background:var(--card);border:1px solid var(--border);border-radius:20px;max-width:900px;width:100%;max-height:88vh;overflow:auto;padding:24px;box-shadow:0 30px 80px rgba(0,0,0,.5)}
.modal .close{float:right;cursor:pointer;color:var(--muted);font-size:24px;line-height:1}
.modal h2{font-size:20px;margin-bottom:6px}
.modal .sub{color:var(--muted);font-size:12px;margin-bottom:14px}
.modal h3{font-size:14px;margin:14px 0 6px;color:var(--accent);font-weight:700}
.modal p{font-size:13px;line-height:1.75;margin-bottom:8px}
.modal .ev{background:var(--surface-0);border:1px solid var(--border);border-radius:10px;padding:10px;margin:6px 0;font-size:12px}
.modal .ev a{color:var(--accent);text-decoration:none}
.modal .ev a:hover{text-decoration:underline}
/* 证据来源标注：方括号内的媒体名 / 可信排名 / 报道时间 */
.ev-src-tag{display:inline-block;font-size:10px;color:var(--accent2-soft);background:var(--surface-2);border:1px solid var(--border);border-radius:6px;padding:1px 7px;margin-left:6px;vertical-align:middle;font-variant-numeric:tabular-nums}
.ev-src-tag .rk{color:var(--ok-text);font-weight:700}
.ev-src-tag .tm{color:var(--muted)}
.modal .media-row{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:8px}
@media(max-width:600px){.modal .media-row{grid-template-columns:1fr}}
.modal .media-cell{background:var(--surface-0);border:1px solid var(--border);border-radius:10px;padding:10px;font-size:12px}
.modal .media-cell .mc-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.modal .media-cell .mc-name{font-weight:700;color:var(--accent)}
.modal .media-cell .mc-status{font-size:10px;padding:2px 6px;border-radius:999px;background:var(--border);color:var(--muted)}
.modal .media-cell .mc-status.hit{background:rgba(34,197,94,.15);color:var(--ok-text)}
.modal .media-cell .mc-link{display:block;margin-top:4px;color:var(--accent);text-decoration:none;font-size:11px}
.modal .media-cell .mc-link:hover{text-decoration:underline}
.empty{color:var(--muted);font-size:13px;padding:24px;text-align:center}
.editable{background:var(--surface-0);border:1px dashed var(--border);border-radius:8px;padding:8px;width:100%;color:var(--text);font-size:13px;font-family:inherit}
.editable:focus{outline:none;border-color:var(--accent);border-style:solid}
.kv{display:grid;grid-template-columns:120px 1fr;gap:6px;font-size:12px;margin:6px 0}
.kv .k{color:var(--muted)}
.note{color:var(--muted);font-size:12px;margin-top:8px;line-height:1.6}

/* methodology section */
.method{margin-top:18px}
.method-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:12px}
@media(max-width:900px){.method-grid{grid-template-columns:1fr}}
.method-card{background:var(--surface-0);border:1px solid var(--border);border-radius:12px;padding:14px}
.method-card h4{color:var(--accent);font-size:13px;margin-bottom:6px;font-weight:700}
.method-card p{font-size:12px;line-height:1.65;color:var(--muted)}
.method-card .src{font-size:10px;color:var(--accent2);margin-top:6px}
.topo{margin-top:14px;background:var(--surface-0);border:1px solid var(--border);border-radius:12px;padding:16px}
.topo svg{width:100%;height:auto}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px;font-size:11px;color:var(--muted)}
.legend span{display:flex;align-items:center;gap:6px}
.legend i{width:10px;height:10px;border-radius:3px;display:inline-block}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid var(--muted);border-top-color:var(--accent);border-radius:50%;animation:spin 1s linear infinite;vertical-align:middle;margin-right:6px}
@keyframes spin{to{transform:rotate(360deg)}}

__MM_CSS__

/* system status panel */
.sys-head{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.sys-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:12px}
.sys-metric{background:var(--surface-0);border:1px solid var(--border);border-radius:12px;padding:12px}
.sys-metric .sm-l{color:var(--muted);font-size:11px;display:flex;align-items:center;gap:6px}
.sys-metric .sm-v{font-size:22px;font-weight:800;margin-top:6px;color:var(--text)}
.sys-metric .sm-bar{height:5px;border-radius:999px;background:var(--border);margin-top:8px;overflow:hidden}
.sys-metric .sm-bar>i{display:block;height:100%;border-radius:999px;transition:width .4s}
.api-table{width:100%;border-collapse:collapse;margin-top:12px;font-size:12px}
.api-table th{text-align:left;color:var(--muted);font-weight:600;padding:8px 10px;border-bottom:1px solid var(--border);font-size:11px}
.api-table td{padding:9px 10px;border-bottom:1px solid var(--border);vertical-align:middle}
.api-table tr:last-child td{border-bottom:none}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:7px;vertical-align:middle}
.dot.on{background:var(--ok);box-shadow:0 0 8px rgba(34,197,94,.6)}
.dot.off{background:var(--bad);box-shadow:0 0 8px rgba(239,68,68,.5)}
.dot.warn{background:var(--warn)}
.api-name{font-weight:600;color:var(--text)}
.api-url{color:var(--muted);font-size:11px;word-break:break-all}
.latency{font-variant-numeric:tabular-nums;font-weight:700}
.latency.good{color:var(--ok)}.latency.slow{color:var(--warn)}.latency.bad{color:var(--bad)}
.sys-foot{color:var(--muted);font-size:11px;margin-top:10px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
.badge-active{display:inline-block;padding:2px 8px;border-radius:999px;background:rgba(34,197,94,.15);color:var(--ok-text);font-size:10px;margin-left:6px}

/* task node timeline inside history list & modal */
.nodes{display:flex;gap:5px;flex-wrap:wrap;margin-top:8px}
.node-chip{font-size:10px;padding:3px 8px;border-radius:6px;background:var(--surface-2);border:1px solid var(--border);color:var(--muted);white-space:nowrap}
.node-chip.done{background:rgba(34,197,94,.12);border-color:rgba(34,197,94,.3);color:var(--ok-text)}
.node-chip.active{background:rgba(56,189,248,.12);border-color:rgba(56,189,248,.35);color:var(--accent-soft)}
.progress-line{font-size:11px;color:var(--muted);margin:4px 0 4px 12px;border-left:2px solid var(--border);padding-left:10px}
.progress-line div{margin:3px 0}
.node-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:8px}
@media(max-width:600px){.node-grid{grid-template-columns:1fr}}
.node-card{background:var(--surface-0);border:1px solid var(--border);border-radius:10px;padding:10px;font-size:12px}
.node-card .nc-h{display:flex;justify-content:space-between;align-items:center;gap:6px}
.node-card .nc-n{font-weight:700;color:var(--accent)}
.node-card .nc-s{font-size:10px;padding:2px 7px;border-radius:999px;background:var(--border);color:var(--muted)}
.node-card .nc-s.done{background:rgba(34,197,94,.15);color:var(--ok-text)}
.node-card .nc-s.active{background:rgba(56,189,248,.15);color:var(--accent-soft)}
.node-card .nc-d{color:var(--muted);font-size:11px;margin-top:5px;line-height:1.5}
</style>
</head>
<body>
<div class="nvds-ambient"></div><div class="nvds-grid"></div>
<div class="wrap">
<header class="topbar">
  <div class="brand">
    <div class="logo">NV</div>
    <div>
      <div class="kicker">NEWSVERIFY · EVIDENCE WORKSPACE</div>
      <h1>新闻事实核查控制台</h1>
      <div class="sub">个人事实核查与持续追踪 · Top 30 公信力媒体交叉验证</div>
    </div>
  </div>
  <div class="header-actions">
    <label class="theme-switch">
      <span>🎨 风格模板</span>
      <select id="themeSelect" onchange="applyTheme(this.value)" aria-label="页面风格模板">
        <option value="aurora">极光 · Aurora</option>
        <option value="paper">纸张 · Paper</option>
        <option value="slate">石墨 · Slate</option>
        <option value="terminal">终端 · Terminal</option>
        <option value="ocean">海洋 · Ocean</option>
        <option value="forest">森林 · Forest</option>
        <option value="sunset">日落 · Sunset</option>
        <option value="violet">紫罗兰 · Violet</option>
        <option value="mono">素黑白 · Mono</option>
      </select>
    </label>
    <button class="music-btn" id="musicBtn" onclick="toggleMusicPanel()" title="背景音乐"><span class="music-note">🎵</span><span id="musicLabel">音乐</span></button>
    <button class="version-btn" onclick="showVersion()" title="查看版本与更新记录"><span class="v-dot"></span>v__APP_VERSION__ · 更新</button>
    <a class="version-btn" href="/admin" title="后台管理"><span>⚙️</span>后台</a>
    <span class="version-btn" title="当前登录账号"><span>👤</span>__USERNAME__</span>
    <a class="version-btn" href="/logout" title="退出登录"><span>↪</span>退出</a>
  </div>
</header>
<div class="nav">
  <a href="#overview">概览</a>
  <a href="#tasks">核查任务</a>
  <a href="#media">媒体观察</a>
  <a href="#system">系统运行</a>
  <a href="#method">方法论</a>
  <a href="/theory">📚 理性查看新闻理论来源</a>
  <a href="https://github.com/zixiang2008/NewsVerify" target="_blank">GitHub / 三语文档</a>
</div>
<span class="section-anchor" id="overview"></span>

<div class="stats" id="stats"></div>

<div class="layout">
  <!-- LEFT: tasks -->
  <div>
    <span class="section-anchor" id="tasks"></span>
    <div class="panel">
      <h2><span class="icon">📝</span>提交核查</h2>
      <textarea id="txt" placeholder="粘贴新闻文字、链接或转发内容…"></textarea>
      <div class="row" style="align-items:center">
        <label style="font-size:12px;color:var(--muted)">核查模式：</label>
        <select id="mode" style="background:var(--surface-0);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:6px 10px;font-size:12px">
          <option value="full">全面核查（主张+证据+Top30媒体）</option>
          <option value="top30">仅 Top 30 媒体核查</option>
          <option value="method">仅跑方法论流水线</option>
        </select>
        <label style="font-size:12px;color:var(--muted);margin-left:8px">更新频率：</label>
        <select id="freq" style="background:var(--surface-0);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:6px 10px;font-size:12px">
          <option value="24h">每天一次</option>
          <option value="6h">每 6 小时</option>
          <option value="week">每周一次</option>
          <option value="none">不追踪</option>
        </select>
      </div>
      <div class="row">
        <button onclick="submit()">开始核查</button>
        <button class="secondary small" onclick="loadEvents()">刷新</button>
      </div>
      <p class="note">核查在后台异步执行，结果通过 Telegram 推送并显示在下方历史中。点击任务可查看详情与最终结果。</p>
    </div>

    <div class="panel" style="margin-top:16px">
      <h2><span class="icon">📜</span>任务历史
        <button class="mini-btn" style="float:right;margin-top:-2px" onclick="showMindmap()" title="以脑图直观查看所有新闻核查与追踪链路">🧠 追踪脑图</button>
      </h2>
      <div class="tabs">
        <div class="tab active" onclick="setFilter('all',this)">全部</div>
        <div class="tab" onclick="setFilter('done',this)">已完成</div>
        <div class="tab" onclick="setFilter('running',this)">进行中</div>
        <div class="tab" onclick="setFilter('failed',this)">失败</div>
      </div>
      <div class="hist" id="events"><div class="empty"><span class="spinner"></span>加载中…</div></div>
    </div>

    <!-- Methodology & topology ~1/4 -->
    <span class="section-anchor" id="method"></span>
    <div class="panel method">
      <h2><span class="icon">🧠</span>方法论、架构与来源</h2>
      <p class="note">本系统的核心方法论、为什么采用、来源与实现方式，以及系统拓扑结构说明。</p>
      <div class="method-grid">
        <div class="method-card">
          <h4>1. 主张拆分 (Claim Decomposition)</h4>
          <p>将新闻拆为可独立验证的原子事实主张，避免整篇新闻混为一谈。每个主张单独判定。</p>
          <div class="src">来源：AVeriTeC / facticli 流水线思想；实现：app/verification/claims.py</div>
        </div>
        <div class="method-card">
          <h4>2. 证据检索与溯源</h4>
          <p>多查询搜索（原始主张 + 反证导向查询）；严格白名单只保留全球公信力靠前的媒体、专业核查机构、搜索引擎入口与权威一手资料；抓取原文并去重。</p>
          <div class="src">来源：Top30 媒体 + Google Fact Check + 搜索引擎；实现：source_policy.py / evidence.py</div>
        </div>
        <div class="method-card">
          <h4>3. 独立性判定</h4>
          <p>转载链不计为多源；通过 independence_chain_id 去重。未找到证据 ≠ 证伪。</p>
          <div class="src">来源：事实核查标准（AVeriTeC）；实现：app/verification/evidence.py</div>
        </div>
        <div class="method-card">
          <h4>4. LLM 判定 (Judge)</h4>
          <p>基于真实检索证据，输出 supported/refuted/mixed/insufficient_evidence/outdated/not_checkable，含反证与缺口。</p>
          <div class="src">来源：OpenAI 兼容结构化输出；实现：app/verification/judge.py</div>
        </div>
        <div class="method-card">
          <h4>5. 六体系元数据</h4>
          <p>NewsGuard/Ad Fontes/AllSides/Reuters/Pew/RSF 仅作为方法学背景，未授权官方数据标记「未接入」，不伪造评分。</p>
          <div class="src">来源：各机构公开方法论；实现：app/ratings/systems.py</div>
        </div>
        <div class="method-card">
          <h4>6. 持续追踪</h4>
          <p>事件/主张级追踪，证据指纹差异检测，仅实质性变化才通知，支持 6h/24h/周，去重与取消。</p>
          <div class="src">来源：任务书追踪规范；实现：app/tracking/*</div>
        </div>
        <div class="method-card">
          <h4>7. 可信来源白名单</h4>
          <p>证据池仅收录公信力靠前的媒体、专业核查机构、全球搜索引擎入口与权威一手资料；百度、QQ、搜狐、虎嗅等聚合站与百科站一律拒绝。</p>
          <div class="src"><button class="mini-btn" onclick="showSourcePolicy()">查看完整白名单 →</button></div>
        </div>
      </div>

      <div class="topo">
        <h3 style="font-size:14px;color:var(--accent);margin-bottom:8px">系统拓扑与结构</h3>
        <svg viewBox="0 0 900 260" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="g1" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="var(--accent)"/><stop offset="1" stop-color="var(--accent2)"/></linearGradient>
            <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="var(--accent)"/></marker>
          </defs>
          <!-- IM entry (all instant messaging platforms) -->
          <rect x="20" y="90" width="150" height="70" rx="10" fill="var(--surface-2)" stroke="var(--accent)" stroke-width="1.5"/>
          <text x="95" y="114" text-anchor="middle" fill="var(--text)" font-size="12" font-weight="700">即时通讯工具</text>
          <text x="95" y="132" text-anchor="middle" fill="var(--muted)" font-size="10">Telegram / Discord / Slack</text>
          <text x="95" y="148" text-anchor="middle" fill="var(--muted)" font-size="10">微信 / 飞书 / 钉钉 等</text>
          <!-- Web -->
          <rect x="20" y="180" width="150" height="50" rx="10" fill="var(--surface-2)" stroke="var(--accent2)"/>
          <text x="95" y="202" text-anchor="middle" fill="var(--text)" font-size="12" font-weight="700">Web UI</text>
          <text x="95" y="218" text-anchor="middle" fill="var(--muted)" font-size="10">new.caishen.today</text>
          <!-- Bot -->
          <rect x="200" y="120" width="140" height="60" rx="12" fill="url(#g1)" opacity=".9"/>
          <text x="270" y="145" text-anchor="middle" fill="var(--surface-0)" font-size="12" font-weight="800">IM 接入适配层</text>
          <text x="270" y="162" text-anchor="middle" fill="var(--surface-0)" font-size="10">多渠道统一入口 · 白名单</text>
          <!-- Worker -->
          <rect x="360" y="60" width="150" height="140" rx="12" fill="var(--surface-2)" stroke="var(--accent3)" stroke-width="1.5"/>
          <text x="435" y="82" text-anchor="middle" fill="var(--accent3)" font-size="13" font-weight="800">Worker</text>
          <text x="435" y="100" text-anchor="middle" fill="var(--muted)" font-size="10">调度 · 核查流水线</text>
          <text x="435" y="120" text-anchor="middle" fill="var(--text)" font-size="10">主张拆分</text>
          <text x="435" y="136" text-anchor="middle" fill="var(--text)" font-size="10">证据检索/溯源</text>
          <text x="435" y="152" text-anchor="middle" fill="var(--text)" font-size="10">Top30 媒体核查</text>
          <text x="435" y="168" text-anchor="middle" fill="var(--text)" font-size="10">LLM 判定</text>
          <text x="435" y="184" text-anchor="middle" fill="var(--text)" font-size="10">追踪/通知</text>
          <!-- DB -->
          <rect x="560" y="90" width="120" height="80" rx="12" fill="var(--surface-2)" stroke="var(--accent2)"/>
          <text x="620" y="118" text-anchor="middle" fill="var(--text)" font-size="12" font-weight="700">PostgreSQL</text>
          <text x="620" y="136" text-anchor="middle" fill="var(--muted)" font-size="10">events/claims/</text>
          <text x="620" y="150" text-anchor="middle" fill="var(--muted)" font-size="10">evidence/verdicts</text>
          <!-- LLM -->
          <rect x="730" y="60" width="130" height="50" rx="10" fill="var(--surface-2)" stroke="var(--warn)"/>
          <text x="795" y="82" text-anchor="middle" fill="var(--text)" font-size="12" font-weight="700">LLM</text>
          <text x="795" y="98" text-anchor="middle" fill="var(--muted)" font-size="10">Magpie / Ollama</text>
          <!-- Search -->
          <rect x="730" y="130" width="130" height="50" rx="10" fill="var(--surface-2)" stroke="var(--warn)"/>
          <text x="795" y="152" text-anchor="middle" fill="var(--text)" font-size="12" font-weight="700">搜索</text>
          <text x="795" y="168" text-anchor="middle" fill="var(--muted)" font-size="10">DuckDuckGo/Brave</text>
          <!-- Top media -->
          <rect x="730" y="200" width="130" height="50" rx="10" fill="var(--surface-2)" stroke="var(--accent3)"/>
          <text x="795" y="222" text-anchor="middle" fill="var(--text)" font-size="12" font-weight="700">Top 30 媒体</text>
          <text x="795" y="238" text-anchor="middle" fill="var(--muted)" font-size="10"> Reuters … WSJ</text>
          <!-- arrows -->
          <line x1="170" y1="125" x2="200" y2="145" stroke="var(--accent)" stroke-width="1.5" marker-end="url(#arrow)"/>
          <line x1="170" y1="205" x2="200" y2="160" stroke="var(--accent2)" stroke-width="1.5" marker-end="url(#arrow)"/>
          <line x1="340" y1="150" x2="360" y2="130" stroke="var(--accent)" stroke-width="1.5" marker-end="url(#arrow)"/>
          <line x1="510" y1="130" x2="560" y2="130" stroke="var(--accent3)" stroke-width="1.5" marker-end="url(#arrow)"/>
          <line x1="680" y1="110" x2="730" y2="85" stroke="var(--warn)" stroke-width="1.2" marker-end="url(#arrow)"/>
          <line x1="680" y1="130" x2="730" y2="155" stroke="var(--warn)" stroke-width="1.2" marker-end="url(#arrow)"/>
          <line x1="680" y1="150" x2="730" y2="225" stroke="var(--accent3)" stroke-width="1.2" marker-end="url(#arrow)"/>
        </svg>
        <div class="legend">
          <span><i style="background:var(--accent)"></i>用户入口</span>
          <span><i style="background:var(--accent3)"></i>处理/存储</span>
          <span><i style="background:var(--warn)"></i>外部依赖</span>
          <span><i style="background:var(--accent2)"></i>Web/展示</span>
        </div>
      </div>
    </div>

    <!-- System status panel -->
    <span class="section-anchor" id="system"></span>
    <div class="panel" style="margin-top:16px">
      <div class="sys-head">
        <h2 style="margin:0"><span class="icon">📊</span>系统运行状况</h2>
        <div style="display:flex;gap:8px;align-items:center">
          <span class="note" style="margin:0" id="sysUpdated">—</span>
          <button class="btn small secondary" onclick="loadSystem()">🔄 刷新</button>
        </div>
      </div>
      <div class="sys-grid" id="sysMetrics">
        <div class="sys-metric"><div class="sm-l">⏳ 采集中…</div></div>
      </div>
      <table class="api-table">
        <thead><tr><th style="width:34%">API / 服务</th><th>地址</th><th style="width:110px">状态</th><th style="width:90px">响应</th></tr></thead>
        <tbody id="sysApis"><tr><td colspan="4" class="note">采集中…</td></tr></tbody>
      </table>
      <div class="sys-foot">
        <span id="sysMeta">当前模型 / 进程信息加载中…</span>
        <span>每 30 秒自动刷新</span>
      </div>
    </div>
  </div>

  <!-- RIGHT: top 10 media -->
  <div class="panel" style="height:fit-content;position:sticky;top:20px">
    <span class="section-anchor" id="media"></span>
    <h2><span class="icon">🌐</span>全球公信力 Top 30 媒体</h2>
    <p class="note">综合 MBFC 事实报道分级、Reuters Institute 信任度研究整理，按“事实准确性 + 编辑独立性”排序，非官方名次。每条新闻核查时会在全部 30 家上交叉验证：<b>🟢 点亮</b>=有报道，<b>⚪ 灰色</b>=未见报道。</p>
    <div class="media-cover" id="mediaSummary">尚未核查任何新闻</div>
    <div class="media-scroll-hint"><span class="sc-line"></span>列表可滚动，查看全部 30 家</div>
    <div class="media-list" id="mediaList"></div>
    <p class="note" id="mediaNote"></p>
  </div>
</div>

</div>

<footer class="footer">
  <div>NewsVerify v__APP_VERSION__ · __RELEASE_DATE__ · __CODENAME__ · 本地优先、证据可追溯的事实核查工作台</div>
  <div class="footer-links">
    <a href="https://github.com/zixiang2008/NewsVerify#readme" target="_blank">English</a>
    <a href="https://github.com/zixiang2008/NewsVerify/blob/main/README.zh-CN.md" target="_blank">中文</a>
    <a href="https://github.com/zixiang2008/NewsVerify/blob/main/README.ja.md" target="_blank">日本語</a>
    <a href="https://github.com/zixiang2008/NewsVerify" target="_blank">GitHub</a>
  </div>
</footer>

<!-- 背景音乐面板 -->
<div class="music-panel" id="musicPanel">
  <h3><span>🎵 背景音乐 · 声景库</span><button class="music-close" onclick="closeMusicPanel()" title="关闭面板">×</button></h3>
  <div class="note" style="margin:2px 0 8px">点一下即播放，再点一下停止 · 5 秒无操作自动收起</div>
  <div class="music-list" id="musicTracks"></div>
  <div class="music-row">
    <button class="mini-btn" onclick="toggleMusic()" id="musicToggleBtn">▶ 播放</button>
    <span>音量</span><input type="range" id="musicVol" min="0" max="100" value="50" oninput="setMusicVolume(this.value)" />
    <span id="musicVolLabel">50%</span>
  </div>
</div>

<!-- Modal -->
<div class="modal-bg" id="modalBg" onclick="closeModal(event)">
  <div class="modal" onclick="event.stopPropagation()">
    <span class="close" onclick="closeModal()">&times;</span>
    <div id="modalContent"></div>
  </div>
</div>

<script>
__SHELL_JS__
const APP_VERSION='__APP_VERSION__';
const STYPE_LABEL={media:'Top30 媒体',fact_checker:'专业核查',search_engine:'搜索引擎',authority:'权威机构',untrusted:'未通过白名单'};
const THEMES=[
  {key:'aurora',name:'极光 · Aurora',desc:'深蓝玻璃质感，默认风格',colors:['#08101f','#38bdf8','#34d399']},
  {key:'paper',name:'纸张 · Paper',desc:'浅色阅读友好风格',colors:['#f5f7fb','#2563eb','#0d9488']},
  {key:'slate',name:'石墨 · Slate',desc:'中性专业的控制台风格',colors:['#0f172a','#60a5fa','#2dd4bf']},
  {key:'terminal',name:'终端 · Terminal',desc:'高对比等宽终端风格',colors:['#050e09','#4ade80','#a3e635']},
  {key:'ocean',name:'海洋 · Ocean',desc:'深海青蓝，沉静通透',colors:['#041420','#22d3ee','#2dd4bf']},
  {key:'forest',name:'森林 · Forest',desc:'自然墨绿，护眼舒缓',colors:['#0a1610','#84cc16','#34d399']},
  {key:'sunset',name:'日落 · Sunset',desc:'暖橙玫红，温暖柔和',colors:['#1e101a','#fb923c','#f472b6']},
  {key:'violet',name:'紫罗兰 · Violet',desc:'深紫优雅，专注沉浸',colors:['#100c20','#c084fc','#e879f9']},
  {key:'mono',name:'素黑白 · Mono',desc:'黑白衬线，纸质阅读',colors:['#fafaf8','#374151','#475569']},
];
function applyTheme(key){
  const found=THEMES.find(t=>t.key===key)||THEMES[0];
  document.documentElement.setAttribute('data-theme',found.key);
  try{localStorage.setItem('nv_theme',found.key);}catch(e){}
  const sel=document.getElementById('themeSelect');
  if(sel) sel.value=found.key;
}
(function initTheme(){
  let saved='aurora';
  try{saved=localStorage.getItem('nv_theme')||'aurora';}catch(e){}
  document.documentElement.setAttribute('data-theme',saved);
  setTimeout(()=>{const sel=document.getElementById('themeSelect'); if(sel) sel.value=saved;},0);
})();
/* ==== v0.6.1 背景音乐：20 种 Web Audio 生成式声景，点击即播放 / 再点即停止 / 5 秒无操作自动淡出 ==== */
const MUSIC_TRACKS=[
  {id:'rain',title:'细雨',en:'Gentle Rain',desc:'柔和雨幕，专注放松',icon:'🌧️',layers:[{kind:'noise',filter:'lowpass',cutoff:1100,gain:0.055,swell:0.15}]},
  {id:'waves',title:'海浪',en:'Ocean Waves',desc:'潮汐起伏，平稳呼吸',icon:'🌊',layers:[{kind:'noise',filter:'lowpass',cutoff:520,gain:0.09,swell:0.75,swellRate:0.16}]},
  {id:'forest',title:'森林',en:'Forest Calm',desc:'空灵和声，宁静自然',icon:'🌲',layers:[{kind:'pad',freq:[261,329,392],wave:'triangle',gain:0.03,swell:0.5}]},
  {id:'night',title:'夜曲',en:'Night Breeze',desc:'低频暖垫，助眠静心',icon:'🌙',layers:[{kind:'pad',freq:[196,246,294],wave:'sine',gain:0.038,swell:0.6}]},
  {id:'whitenoise',title:'白噪音',en:'White Noise',desc:'均匀频谱，遮蔽杂音',icon:'🌫️',layers:[{kind:'noise',gain:0.022}]},
  {id:'bowl',title:'颂钵',en:'Singing Bowl',desc:'泛音轻击，冥想静心',icon:'🪔',layers:[{kind:'strike',freq:[220,440,653,880],gain:0.06,interval:5200,decay:5.5}]},
  {id:'zen',title:'佛教庭院',en:'Zen Garden',desc:'钟磬与庭鸟，禅意空间',icon:'⛩️',layers:[{kind:'strike',freq:[174,348,523],gain:0.05,interval:6800,decay:6},{kind:'chirp',freq:[1200,1800],gain:0.012,interval:2600}]},
  {id:'birds',title:'室外鸟叫',en:'Morning Birds',desc:'晨间啁啾，清新自然',icon:'🐦',layers:[{kind:'chirp',freq:[1400,2300],gain:0.02,interval:1000}]},
  {id:'thunder',title:'雷雨',en:'Thunder Rain',desc:'雨幕低雷，沉稳安心',icon:'⛈️',layers:[{kind:'noise',filter:'lowpass',cutoff:700,gain:0.07,swell:0.3},{kind:'strike',freq:[55,82],gain:0.045,interval:11000,decay:3}]},
  {id:'stream',title:'溪流',en:'Mountain Stream',desc:'山涧流水，清透灵动',icon:'🏞️',layers:[{kind:'noise',filter:'bandpass',cutoff:1800,q:0.7,gain:0.06,swell:0.2}]},
  {id:'chimes',title:'风铃',en:'Wind Chimes',desc:'随风轻响，清脆空灵',icon:'🎐',layers:[{kind:'strike',freq:[880,1320,1760],gain:0.035,interval:3000,decay:2.4}]},
  {id:'crickets',title:'夏夜虫鸣',en:'Summer Crickets',desc:'草间细鸣，乡野夜色',icon:'🦗',layers:[{kind:'chirp',freq:[3800,4600],gain:0.014,interval:700,burst:3}]},
  {id:'fire',title:'篝火',en:'Campfire',desc:'木柴噼啪，温暖休憩',icon:'🔥',layers:[{kind:'noise',filter:'lowpass',cutoff:1600,gain:0.035,swell:0.25}]},
  {id:'deep',title:'深海',en:'Deep Ocean',desc:'极低频垫，沉浸放空',icon:'🐋',layers:[{kind:'pad',freq:[55,82,110],wave:'sine',gain:0.05,swell:0.7,rate:0.05}]},
  {id:'mist',title:'晨雾',en:'Morning Mist',desc:'薄雾和声，柔和舒展',icon:'🌅',layers:[{kind:'pad',freq:[293,369,440],wave:'sine',gain:0.028,swell:0.5}]},
  {id:'leaves',title:'雨打芭蕉',en:'Rain on Leaves',desc:'叶面雨滴，细腻清脆',icon:'🍃',layers:[{kind:'noise',filter:'bandpass',cutoff:2600,q:1.2,gain:0.05,swell:0.2}]},
  {id:'bell',title:'寺院钟声',en:'Temple Bell',desc:'悠远钟鸣，庄严宁静',icon:'🔔',layers:[{kind:'strike',freq:[110,220,330,440],gain:0.055,interval:9000,decay:8}]},
  {id:'moon',title:'月光',en:'Moonlight',desc:'空灵长音，夜色温柔',icon:'🌕',layers:[{kind:'pad',freq:[220,277,330,415],wave:'sine',gain:0.024,swell:0.55,rate:0.07}]},
  {id:'bamboo',title:'竹林',en:'Bamboo Grove',desc:'风过竹叶，偶有鸟语',icon:'🎋',layers:[{kind:'noise',filter:'bandpass',cutoff:2200,q:0.6,gain:0.04,swell:0.5},{kind:'chirp',freq:[1600,2400],gain:0.012,interval:4200}]},
  {id:'snow',title:'雪落',en:'Falling Snow',desc:'极轻高频，安静入睡',icon:'❄️',layers:[{kind:'noise',filter:'highpass',cutoff:4200,gain:0.022,swell:0.25}]},
];
let nvAudioCtx=null,nvLayers=[],nvMusicOn=false,nvCurrentTrack='rain',nvMusicVol=0.5,nvMusicHideTimer=null;
function nvEnsureAudio(){
  if(!nvAudioCtx){
    const AC=window.AudioContext||window.webkitAudioContext;
    if(!AC) throw new Error('Web Audio unavailable');
    nvAudioCtx=new AC();
    const master=nvAudioCtx.createGain(); master.gain.value=nvMusicVol; master.connect(nvAudioCtx.destination);
    nvAudioCtx._master=master;
  }
  if(nvAudioCtx.state==='suspended') nvAudioCtx.resume();
  return nvAudioCtx;
}
function nvBuildLayer(layer){
  const ctx=nvAudioCtx,master=ctx._master;
  const bus=ctx.createGain(); bus.gain.value=layer.gain; bus.connect(master);
  const h={bus:bus,nodes:[],timers:[]};
  if(layer.kind==='noise'){
    const len=Math.floor(ctx.sampleRate*3);
    const buf=ctx.createBuffer(1,len,ctx.sampleRate);
    const data=buf.getChannelData(0);
    for(let i=0;i<len;i++) data[i]=Math.random()*2-1;
    const src=ctx.createBufferSource(); src.buffer=buf; src.loop=true;
    let tail=src;
    if(layer.filter){
      const f=ctx.createBiquadFilter(); f.type=layer.filter; f.frequency.value=layer.cutoff||1000;
      if(layer.q) f.Q.value=layer.q;
      src.connect(f); tail=f; h.nodes.push(f);
    }
    tail.connect(bus); src.start(); h.nodes.push(src);
    if(layer.swell){
      let ph=Math.random()*6.28;
      const rate=layer.swellRate||0.12;
      const timer=setInterval(()=>{
        ph+=rate;
        const env=1-layer.swell+layer.swell*(0.5+0.5*Math.sin(ph));
        bus.gain.setTargetAtTime(layer.gain*env,ctx.currentTime,0.7);
      },1200);
      h.timers.push(timer);
    }
  }else if(layer.kind==='pad'){
    (layer.freq||[220]).forEach((f,i)=>{
      const osc=ctx.createOscillator(); osc.type=layer.wave||'sine'; osc.frequency.value=f;
      const g=ctx.createGain(); g.gain.value=0.0001;
      osc.connect(g); g.connect(bus); osc.start();
      h.nodes.push(osc); h.nodes.push(g);
      g.gain.setTargetAtTime(layer.gain*0.7,ctx.currentTime,1.2);
      let ph=Math.random()*6.28;
      const rate=layer.rate||0.1;
      const timer=setInterval(()=>{
        ph+=rate;
        const env=0.42+0.58*(0.5+0.5*Math.sin(ph+i*0.7));
        g.gain.setTargetAtTime(layer.gain*env,ctx.currentTime,1.2);
      },1400);
      h.timers.push(timer);
    });
  }else if(layer.kind==='chirp'){
    const beat=()=>{
      const now=ctx.currentTime;
      const base=(layer.freq||[1600])[0]*(0.85+Math.random()*0.3);
      const osc=ctx.createOscillator(); osc.type='sine';
      const g=ctx.createGain();
      osc.frequency.setValueAtTime(base,now);
      osc.frequency.exponentialRampToValueAtTime(base*(1.25+Math.random()*0.35),now+0.07);
      osc.frequency.exponentialRampToValueAtTime(base*0.8,now+0.19);
      const peak=layer.gain*(0.6+Math.random()*0.8);
      g.gain.setValueAtTime(0.0001,now);
      g.gain.exponentialRampToValueAtTime(peak,now+0.025);
      g.gain.exponentialRampToValueAtTime(0.0001,now+0.24);
      osc.connect(g); g.connect(bus); osc.start(now); osc.stop(now+0.26);
    };
    const burst=layer.burst||1;
    const timer=setInterval(()=>{for(let k=0;k<burst;k++) setTimeout(beat,k*90);},layer.interval||1200);
    h.timers.push(timer);
    setTimeout(beat,300);
  }else if(layer.kind==='strike'){
    const beat=()=>{
      const now=ctx.currentTime;
      (layer.freq||[220]).forEach((f,i)=>{
        const osc=ctx.createOscillator(); osc.type=layer.wave||'sine';
        osc.frequency.value=f*(1+(Math.random()-0.5)*0.004);
        const g=ctx.createGain();
        const a=layer.gain/(i+1.2),dec=layer.decay||4;
        g.gain.setValueAtTime(0.0001,now);
        g.gain.exponentialRampToValueAtTime(Math.max(0.0002,a),now+0.03);
        g.gain.exponentialRampToValueAtTime(0.0001,now+dec);
        osc.connect(g); g.connect(bus); osc.start(now); osc.stop(now+dec+0.1);
      });
    };
    const timer=setInterval(beat,layer.interval||6000);
    h.timers.push(timer);
    beat();
  }
  return h;
}
function nvDestroyLayers(){
  nvLayers.forEach(h=>{
    h.timers.forEach(t=>clearInterval(t));
    h.nodes.forEach(n=>{try{if(n.stop)n.stop();}catch(e){}try{n.disconnect();}catch(e){}});
    try{h.bus.disconnect();}catch(e){}
  });
  nvLayers=[];
}
function updateMusicUI(){
  const btn=document.getElementById('musicBtn'); if(btn) btn.classList.toggle('playing',nvMusicOn);
  const lbl=document.getElementById('musicLabel'); if(lbl) lbl.textContent=nvMusicOn?'播放中':'音乐';
  const tb=document.getElementById('musicToggleBtn'); if(tb) tb.textContent=nvMusicOn?'⏸ 停止':'▶ 播放';
}
function renderMusicTracks(){
  const box=document.getElementById('musicTracks'); if(!box) return;
  box.innerHTML=MUSIC_TRACKS.map(t=>{
    const playing=nvMusicOn&&t.id===nvCurrentTrack;
    return `<div class="music-track ${playing?'active':''}" onclick="selectMusic('${t.id}')" title="${playing?'再点一下停止':'点击播放'}">
       <div><div class="mt-title">${t.icon} ${t.title}<span style="font-weight:400;opacity:.55"> · ${t.en}</span></div><div class="mt-desc">${t.desc}</div></div>
       <span class="mt-icon">${playing?'🔊':'▶'}</span>
     </div>`;
  }).join('');
}
function selectMusic(id){
  if(nvMusicOn&&nvCurrentTrack===id) stopMusic(); else startMusic(id);
  resetMusicPanelHideTimer();
}
function startMusic(id){
  try{
    nvEnsureAudio();
    nvDestroyLayers();
    if(id&&MUSIC_TRACKS.some(x=>x.id===id)){
      nvCurrentTrack=id;
      try{localStorage.setItem('nv_music_track',id);}catch(e){}
    }
    const t=MUSIC_TRACKS.find(x=>x.id===nvCurrentTrack)||MUSIC_TRACKS[0];
    t.layers.forEach(l=>nvLayers.push(nvBuildLayer(l)));
    nvMusicOn=true;
    updateMusicUI(); renderMusicTracks();
  }catch(e){ console.warn('music start failed',e); }
}
function stopMusic(){
  nvDestroyLayers();
  nvMusicOn=false;
  updateMusicUI(); renderMusicTracks();
}
function setMusicVolume(v){
  nvMusicVol=Math.max(0,Math.min(1,Number(v)/100));
  if(nvAudioCtx&&nvAudioCtx._master) nvAudioCtx._master.gain.setTargetAtTime(nvMusicVol,nvAudioCtx.currentTime,0.05);
  const lbl=document.getElementById('musicVolLabel'); if(lbl) lbl.textContent=Math.round(nvMusicVol*100)+'%';
  try{localStorage.setItem('nv_music_vol',String(Math.round(nvMusicVol*100)));}catch(e){}
  resetMusicPanelHideTimer();
}
function toggleMusic(){
  if(nvMusicOn) stopMusic(); else startMusic();
  resetMusicPanelHideTimer();
}
function openMusicPanel(){
  const p=document.getElementById('musicPanel'); if(!p) return;
  if(nvMusicHideTimer){clearTimeout(nvMusicHideTimer);nvMusicHideTimer=null;}
  p.classList.remove('hide');
  p.style.display='block';
  void p.offsetWidth;
  p.classList.add('show');
  const vol=document.getElementById('musicVol'); if(vol) vol.value=Math.round(nvMusicVol*100);
  const lbl=document.getElementById('musicVolLabel'); if(lbl) lbl.textContent=Math.round(nvMusicVol*100)+'%';
  renderMusicTracks();
  resetMusicPanelHideTimer();
}
function closeMusicPanel(){
  const p=document.getElementById('musicPanel'); if(!p||p.style.display==='none') return;
  if(nvMusicHideTimer){clearTimeout(nvMusicHideTimer);nvMusicHideTimer=null;}
  p.classList.remove('show'); p.classList.add('hide');
  setTimeout(()=>{if(p.classList.contains('hide')) p.style.display='none';},360);
}
function resetMusicPanelHideTimer(){
  if(nvMusicHideTimer) clearTimeout(nvMusicHideTimer);
  nvMusicHideTimer=setTimeout(closeMusicPanel,5000);
}
function toggleMusicPanel(){
  const p=document.getElementById('musicPanel');
  if(p&&p.style.display==='block'&&!p.classList.contains('hide')) closeMusicPanel(); else openMusicPanel();
}
(function initMusic(){
  try{
    const t=localStorage.getItem('nv_music_track'); if(t&&MUSIC_TRACKS.some(x=>x.id===t)) nvCurrentTrack=t;
    const v=localStorage.getItem('nv_music_vol'); if(v!=null) nvMusicVol=Math.max(0,Math.min(1,Number(v)/100));
  }catch(e){}
  setTimeout(()=>{
    const p=document.getElementById('musicPanel');
    if(p) ['click','mousemove','input','wheel','touchstart'].forEach(ev=>p.addEventListener(ev,resetMusicPanelHideTimer,{passive:true}));
    const vol=document.getElementById('musicVol'); if(vol) vol.value=Math.round(nvMusicVol*100);
    const lbl=document.getElementById('musicVolLabel'); if(lbl) lbl.textContent=Math.round(nvMusicVol*100)+'%';
  },0);
})();
async function showVersion(){
  const modalBg=document.getElementById('modalBg');
  const box=document.getElementById('modalContent');
  box.innerHTML='<h2>版本与更新记录</h2><div class="sub">正在加载版本信息…</div>';
  modalBg.style.display='flex';
  try{
    const r=await fetch('/api/version');
    const d=await r.json();
    let html=`<h2>版本与更新记录 <span class="badge">v${esc(d.version)}</span></h2>`;
    html+=`<div class="sub">${esc(d.release_date)} · ${esc(d.codename)} · 当前界面主题：${esc((THEMES.find(t=>t.key===document.documentElement.getAttribute('data-theme'))||THEMES[0]).name)}</div>`;
    html+=`<h3>可切换的页面风格模板</h3><div class="media-row">`;
    for(const t of d.themes||THEMES){
      const sample=(THEMES.find(x=>x.key===t.key)||{colors:['#eee','#888','#555']}).colors;
      html+=`<div class="media-cell"><div class="mc-head"><span class="mc-name">${esc(t.name)}</span>`+
        `<span class="mc-status">${document.documentElement.getAttribute('data-theme')===t.key?'使用中':'可切换'}</span></div>`+
        `<div class="theme-sample">${sample.map(c=>`<i style="background:${c}"></i>`).join('')}</div>`+
        `<div class="note" style="margin-top:5px">${esc(t.description)}</div></div>`;
    }
    html+=`</div><h3>更新历史</h3>`;
    for(const rel of d.releases||[]){
      html+=`<div class="release-item"><div class="release-head"><b>v${esc(rel.version)} · ${esc(rel.codename)}</b><span class="note">${esc(rel.date)}</span></div>`+
        `<div class="note">${esc(rel.summary)}</div><ul>${(rel.changes||[]).map(c=>`<li>${esc(c)}</li>`).join('')}</ul></div>`;
    }
    html+=`<div class="note">Top 媒体样本：${d.top_media_count||30} 家 · 文档：English / 中文 / 日本語 · 源码：GitHub 同步</div>`;
    box.innerHTML=html;
  }catch(e){
    box.innerHTML=`<h2>版本与更新记录</h2><div class="sub">当前版本 v${APP_VERSION}</div><p class="note">版本详情加载失败：${esc(e.message)}</p>`;
  }
}
async function showSourcePolicy(){
  const bg=document.getElementById('modalBg'),box=document.getElementById('modalContent');
  box.innerHTML='<h2>可信来源白名单</h2><div class="sub">正在加载白名单…</div>';bg.style.display='flex';
  try{
    const d=await(await fetch('/api/source-policy')).json();
    const group=(title,arr,fmt)=>`<h3>${esc(title)}（${arr.length}）</h3><div class="note" style="line-height:1.9">${arr.map(x=>esc(fmt(x))).join(' · ')}</div>`;
    let html=`<h2>可信来源白名单 <span class="badge">Strict Whitelist</span></h2>`;
    html+=`<div class="sub">${esc(d.note)}</div>`;
    html+=group('① 全球公信力 Top 30 媒体',d.media,x=>x.name+' ('+x.domain+')');
    html+=group('② 专业事实核查机构',d.fact_checkers,x=>x);
    html+=group('③ 全球搜索引擎入口',d.search_engines,x=>x);
    html+=group('④ 权威一手资料机构',d.authorities,x=>x);
    html+=`<h3>明确拒绝的来源</h3><div class="note" style="line-height:1.9">${d.blocked_examples.map(x=>esc(x)).join(' · ')}</div>`;
    box.innerHTML=html;
  }catch(e){
    box.innerHTML=`<h2>可信来源白名单</h2><p class="note">加载失败：${esc(e.message)}</p>`;
  }
}
let allEvents=[]; let filter='all';
async function loadStats(){
  const r=await fetch('/api/status');const d=await r.json();
  document.getElementById('stats').innerHTML=
    `<div class="card stat"><div class="n">${d.events}</div><div class="l">事件数</div></div>`+
    `<div class="card stat"><div class="n">${d.jobs}</div><div class="l">任务数</div></div>`+
    `<div class="card stat"><div class="n">${d.active_subscriptions}</div><div class="l">活跃追踪</div></div>`+
    `<div class="card stat"><div class="n">__TOP_MEDIA_COUNT__</div><div class="l">核查媒体</div></div>`;
}
// ---------- 系统运行状况 ----------
const NODE_DEFS=[
  {key:'claims',name:'主张拆分',desc:'把新闻拆为可独立验证的原子事实主张'},
  {key:'evidence',name:'证据检索与溯源',desc:'多查询检索原文、去重、记录来源'},
  {key:'independence',name:'独立性判定',desc:'折叠转载链，独立来源才计数'},
  {key:'judge',name:'LLM 判定',desc:'supported/refuted/mixed 等六类结论'},
  {key:'ratings',name:'媒体交叉核查',desc:'Top30 公信力媒体交叉验证，记录报道来源'},
  {key:'tracking',name:'持续追踪',desc:'证据指纹变化检测，实质变化才通知'},
];
function nodeState(progress,claimCount,verdictCount,eviCount,hasTopMedia,subs){
  // 依据 worker 实际写入的 progress 步骤推断各节点状态
  const steps=(progress||[]).map(p=>p.step||'');
  const joined=steps.join(' | ');
  const has=(kw)=>joined.includes(kw);
  const st=(done,active)=>done?'done':(active?'active':'');
  return [
    {key:'claims',state:st(has('主张拆分')||claimCount>0,has('收到任务'))},
    {key:'evidence',state:st(has('证据收集')||eviCount>0,has('主张拆分'))},
    {key:'independence',state:st(has('证据收集')||eviCount>0,has('证据收集'))},
    {key:'judge',state:st(verdictCount>0||has('判定'),has('证据收集'))},
    {key:'ratings',state:st(has('Top 30')||has('Top 10')||hasTopMedia,verdictCount>0)},
    {key:'tracking',state:st((subs||0)>0,false)},
  ];
}
const NODE_LABEL={claims:'主张拆分',evidence:'证据检索',independence:'独立性判定',judge:'LLM判定',ratings:'媒体交叉核查',tracking:'持续追踪'};
function latencyClass(ms){if(ms==null)return 'bad';if(ms<1000)return 'good';if(ms<3000)return 'slow';return 'bad';}
async function loadSystem(){
  try{
    const r=await fetch('/api/system');
    if(!r.ok) throw new Error('HTTP '+r.status);
    const d=await r.json();
    // metrics
    const sys=d.system||{};
    const metrics=[
      {l:'🖥️ CPU 使用率',v:sys.cpu_percent!=null?sys.cpu_percent+'%':'N/A',pct:sys.cpu_percent,color:'var(--accent)'},
      {l:'🧠 内存使用',v:(sys.memory_used_pct!=null?sys.memory_used_pct+'%':'N/A'),pct:sys.memory_used_pct,color:'var(--accent2)'},
      {l:'💾 磁盘使用',v:sys.disk&&sys.disk.used_pct!=null?sys.disk.used_pct+'%':'N/A',pct:sys.disk?sys.disk.used_pct:null,color:'var(--accent3)'},
      {l:'⏱️ 运行时长',v:fmtUptime(d.uptime_seconds),pct:null,color:'var(--ok)'},
    ];
    document.getElementById('sysMetrics').innerHTML=metrics.map(m=>
      `<div class="sys-metric"><div class="sm-l">${m.l}</div><div class="sm-v">${m.v}</div>`+
      (m.pct!=null?`<div class="sm-bar"><i style="width:${Math.min(100,Math.max(0,m.pct))}%;background:${m.color}"></i></div>`:'')+
      `</div>`).join('');
    // apis
    const rows=(d.apis||[]).map(a=>{
      const dot=a.online?'on':'off';
      const lat=a.latency_ms!=null?`<span class="latency ${latencyClass(a.latency_ms)}">${a.latency_ms}ms</span>`:'<span class="latency bad">—</span>';
      const normUrl=u=>String(u||'').replace(/[/]+$/,'');
      const active=(d.active_llm_endpoint&&a.url&&normUrl(d.active_llm_endpoint)===normUrl(a.url))?'<span class="badge-active">生效中</span>':'';
      return `<tr><td><span class="dot ${dot}"></span><span class="api-name">${a.name}</span>${active}</td>`+
        `<td class="api-url">${a.url||'—'}<br><span style="color:var(--muted)">${a.detail||''}</span></td>`+
        `<td>${a.online?'<span style="color:var(--ok)">在线</span>':'<span style="color:var(--bad)">离线</span>'}</td>`+
        `<td>${lat}</td></tr>`;
    }).join('');
    document.getElementById('sysApis').innerHTML=rows||'<tr><td colspan="4" class="note">未检测到外部 API 配置</td></tr>';
    const cfg=d.config||{};
    document.getElementById('sysMeta').textContent=
      `模型 ${cfg.llm_model||'-'} · 判定 ${cfg.judge_model||'-'} · 搜索 ${cfg.search_provider||'-'} · 进程RSS ${sys.process_rss_mb!=null?sys.process_rss_mb+'MB':'-'}`;
    document.getElementById('sysUpdated').textContent='更新于 '+new Date().toLocaleTimeString();
  }catch(e){ console.error('loadSystem',e); }
}
function fmtUptime(sec){
  if(sec==null)return '-';
  if(sec<60)return sec+'秒';
  if(sec<3600)return Math.floor(sec/60)+'分';
  if(sec<86400)return Math.floor(sec/3600)+'小时'+Math.floor((sec%3600)/60)+'分';
  return Math.floor(sec/86400)+'天'+Math.floor((sec%86400)/3600)+'小时';
}
async function loadMedia(){
  const r=await fetch('/api/top-media');const d=await r.json();
  window._mediaDefs=d.media;
  document.getElementById('mediaList').innerHTML=d.media.map(m=>
    `<div class="media-item" id="mi-${m.rank}">
       <div class="head"><span class="name"><span class="ml-dot" id="dot-${m.rank}"></span>${m.rank}. ${m.name}</span><span class="rank">${m.factual||''}</span></div>
       <a href="${m.url}" target="_blank">${m.url.replace('https://www.','')}</a>
       <div class="why">${m.why||''}</div>
       <div class="status miss" id="ms-${m.rank}">⚪ 未核查</div>
     </div>`).join('');
  document.getElementById('mediaNote').textContent=d.note;
}
function updateMediaStatus(topMedia){
  if(!topMedia||!topMedia.length) return;
  let hits=0,reports=0;
  for(const m of topMedia){
    const item=document.getElementById('mi-'+m.rank);
    const dot=document.getElementById('dot-'+m.rank);
    const el=document.getElementById('ms-'+m.rank);
    const n=Number(m.hit_count||0);
    if(n>0){hits++;reports+=n;}
    if(item) item.classList.toggle('reported',n>0);
    if(dot) dot.classList.toggle('lit',n>0);
    if(el){ el.textContent = n? `🟢 ${n} 条相关报道` : '⚪ 未见报道'; el.className='status '+(n?'hit':'miss'); }
  }
  // 顶部汇总
  const s=document.getElementById('mediaSummary');
  if(s) s.innerHTML=`<span class="ml-dot lit"></span> 最近核查：<b>${hits}</b> / ${topMedia.length} 家媒体有报道 · 共 <b>${reports}</b> 条来源`;
}
async function loadEvents(){
  try{
    const r=await fetch('/api/events');
    if(!r.ok) return;
    allEvents=await r.json();
    renderEvents();
  }catch(e){ console.error(e); }
}
function setFilter(f,el){filter=f;document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));el.classList.add('active');renderEvents();}
function renderEvents(){
  let data=Array.isArray(allEvents)?allEvents:[];
  if(filter!=='all') data=data.filter(e=> (filter==='running'?(e.job_status==='running'||e.job_status==='queued'):e.job_status===filter));
  const el=document.getElementById('events');
  if(!el) return;
  if(!data.length){el.innerHTML='<div class="empty">暂无任务</div>';return;}
  el.innerHTML=data.map(e=>{
    try{
      const st=e.job_status||e.status||'unknown';
      const preview=esc((e.title||'').slice(0,90));
      const claims=Array.isArray(e.claims)?e.claims:[];
      const verdicts=Array.isArray(e.verdicts)?e.verdicts:[];
      const verdict=verdicts.length?verdicts[0]:null;
      const vtag=verdict?`<span class="tag ${verdict.label}">${verdict.label}</span>`:'';
      const jr=e.job_result||{};
      const summary=jr.summary?esc(String(jr.summary).slice(0,160)):'';
      const progress=jr.progress||[];
      const lastStep=progress.length?progress[progress.length-1]:null;
      const evidCount=progress.filter(p=>(p.step||'').includes('证据收集')).length;
      const nodeStates=nodeState(progress,claims.length,verdicts.length,evidCount,jr.top_media,e.active_subs||0);
      const chips=nodeStates.map(n=>`<span class="node-chip ${n.state}" title="${NODE_DEFS.find(d=>d.key===n.key)?.desc||''}">${NODE_LABEL[n.key]}</span>`).join('');
      const stCls=['done','running','queued','failed'].includes(st)?st:'';
      const mediaHits=jr.media_hits||0;
      const totalRpt=jr.total_reports||0;
      return `<div class="hitem" onclick="showDetail('${e.id}')">
        <div class="top">
          <div class="title" contenteditable="true" onblur="saveTitle('${e.id}',this)">${preview}</div>
          <div style="display:flex;gap:6px;align-items:center">
            <span class="tag ${stCls}">${st}</span>
            <button class="btn small secondary" onclick="event.stopPropagation();deleteEvent('${e.id}')" title="删除">🗑</button>
          </div>
        </div>
        <div class="meta">
          <span>${String(e.id||'').slice(0,8)}</span>
          <span>${e.created_at?new Date(e.created_at).toLocaleString():''}</span>
          ${vtag}
          <span>主张 ${claims.length}</span>
          ${jr.top_media?`<span style="color:var(--ok-text)">🟢 ${mediaHits}/30 媒体报道 · ${totalRpt} 条来源</span>`:''}
        </div>
        ${lastStep?`<div class="meta"><span style="color:var(--accent)">▸ ${esc(lastStep.step)}</span></div>`:''}
        <div class="nodes">${chips}</div>
        ${summary?`<div class="note" style="margin-top:6px">${summary}</div>`:''}
        <div class="mm-mini-wrap">
          <div class="mm-mini-head"><span>🧠 本条新闻的专属脑图</span>
            <span style="cursor:pointer;color:var(--accent)" onclick="event.stopPropagation();showMindmap('${e.id}')">展开完整脑图 ↗</span></div>
          <div id="mmmini-${e.id}" onclick="event.stopPropagation();showMindmap('${e.id}')"
               title="点击打开该新闻的六维度连线脑图"></div>
        </div>
        <div class="card-actions">
          <button class="mini-btn" onclick="event.stopPropagation();showMindmap('${e.id}')" title="查看这条新闻的完整脑图">🧠 脑图</button>
          <button class="mini-btn track" onclick="event.stopPropagation();showTrackStatus('${e.id}')" title="查看该新闻的追踪状态与所有更新汇总">📡 追踪状态</button>
          <button class="mini-btn setting" onclick="event.stopPropagation();showTrackSettings('${e.id}')" title="修改追踪约定、频率与时间">⚙️ 设置</button>
        </div>
      </div>`;
    }catch(err){ console.error('renderEvents item',err,e); return ''; }
  }).join('');
  mmRenderMinis();
}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function saveTitle(id,el){
  const t=el.innerText.trim();
  await fetch('/api/events/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:t})});
}
async function showDetail(id){
  const r=await fetch('/api/events/'+id);const d=await r.json();
  if(!d||!d.id){alert('事件不存在');return;}
  d.claims=Array.isArray(d.claims)?d.claims:[];
  d.jobs=Array.isArray(d.jobs)?d.jobs:[];
  d.subscriptions=Array.isArray(d.subscriptions)?d.subscriptions:[];
  const latestJob=d.jobs[0]||{};
  const jr=latestJob.result||{};
  const eviCount=d.claims.reduce((n,c)=>n+((c.evidence||[]).length),0);
  const verdictCount=d.claims.filter(c=>c.verdict).length;
  const nodeStates=nodeState(jr.progress,d.claims.length,verdictCount,eviCount,jr.top_media,d.subscriptions.filter(s=>s.active).length);
  let html=`<h2>事件详情 <span class="badge">${d.id.slice(0,8)}</span></h2>`;
  html+=`<div class="sub">${esc(d.title)}</div>`;
  html+=`<div class="kv"><div class="k">状态</div><div><span class="tag ${['done','running','queued','failed'].includes(latestJob.status||d.status)?(latestJob.status||d.status):''}">${latestJob.status||d.status}</span></div>`+
    `<div class="k">创建时间</div><div>${d.created_at?new Date(d.created_at).toLocaleString():''}</div></div>`;
  // 6 大方法节点卡片
  html+=`<h3>核查流程节点（6 个步骤）</h3><div class="node-grid">`;
  nodeStates.forEach((n,i)=>{
    const def=NODE_DEFS[i];
    const label={done:'✅ 完成',active:'🔄 进行中','' :'⏸ 未开始'}[n.state]||'⏸ 未开始';
    html+=`<div class="node-card"><div class="nc-h"><span class="nc-n">${i+1}. ${def.name}</span>`+
      `<span class="nc-s ${n.state}">${label}</span></div><div class="nc-d">${def.desc}</div></div>`;
  });
  html+=`</div>`;
  // 实时进度时间线
  if(jr.progress&&jr.progress.length){
    html+=`<h3>处理进度</h3><div style="margin:8px 0 4px 12px;border-left:2px solid var(--accent);padding-left:12px">`;
    for(const p of jr.progress){
      html+=`<div style="font-size:12px;color:var(--muted);margin:4px 0"><span style="color:var(--accent)">⏱</span> ${p.time?new Date(p.time).toLocaleTimeString():''} — ${esc(p.step)}</div>`;
    }
    if(latestJob.status==='running'||latestJob.status==='queued') html+=`<div style="font-size:11px;color:var(--accent)" class="note"><span class="spinner"></span>后台正在处理，本弹窗约每 3 秒自动刷新…</div>`;
    html+=`</div>`;
  }
  // editable title
  html+=`<div style="margin:8px 0"><input class="editable" id="editTitle" value="${(d.title||'').replace(/"/g,'&quot;')}" /><button class="btn small" style="margin-left:8px" onclick="saveTitleFromModal('${d.id}')">保存修改</button></div>`;
  // summary
  if(d.summary) html+=`<div class="note" style="margin:8px 0"><b>总结：</b>${esc(d.summary)}</div>`;
  // claims + verdicts
  for(const c of d.claims){
    html+=`<h3>主张：${esc(c.text)}</h3>`;
    if(c.verdict){
      const v=c.verdict;
      html+=`<p><span class="tag ${esc(v.label)}">${esc(v.label)}</span> 置信度 ${(v.confidence*100).toFixed(0)}%</p>`;
      html+=`<p>${esc(v.rationale)}</p>`;
      if(v.counter_argument) html+=`<p><b>反证：</b>${esc(v.counter_argument)}</p>`;
      if(v.evidence_gaps&&v.evidence_gaps.length) html+=`<p><b>缺口：</b>${esc(v.evidence_gaps.join('；'))}</p>`;
    }
    if(c.evidence&&c.evidence.length){
      html+=`<h3>证据（${c.evidence.length}）</h3>`;
      for(const ev of c.evidence){
        let tag='';
        if(ev.media_rank){
          const tm=ev.reported_at?String(ev.reported_at).slice(0,10):'时间未标注';
          tag=`<span class="ev-src-tag">[ <span class="rk">全球可信榜第 ${ev.media_rank} 名 · ${esc(ev.media_name||'')} · ${esc(ev.factual||'')}</span> · <span class="tm">${esc(tm)}</span> ]</span>`;
        }else{
          const tm=ev.reported_at?String(ev.reported_at).slice(0,10):'时间未标注';
          tag=`<span class="ev-src-tag">[ ${esc(STYPE_LABEL[ev.source_type]||ev.source_type||'来源')} · 非 Top30 榜单 · <span class="tm">${esc(tm)}</span> ]</span>`;
        }
        html+=`<div class="ev"><a href="${ev.url}" target="_blank">${ev.title||ev.domain}</a>${tag}<br>${(ev.snippet||'').slice(0,220)}</div>`;
      }
    }
  }
  // Top30 媒体覆盖（首条主张汇总 + 逐条主张明细）
  if(d.top_media&&d.top_media.length){
    const hits=d.media_hits||0,reports=d.total_reports||0;
    html+=`<h3>🌐 媒体覆盖 · Top 30（${hits} 家报道 / ${reports} 条来源）</h3>`;
    html+=`<div class="media-cover"><span class="ml-dot lit"></span> 点亮=有报道，灰色=未见报道；点击来源可打开原文</div>`;
    // 聚合视图：30 家灯 + 来源
    html+=`<div class="media-row">`;
    for(const m of d.top_media){
      const n=Number(m.hit_count||0);
      const lit=n>0;
      const links=lit&&m.hits&&m.hits.length
        ? `<div class="src-list">${m.hits.map(h=>`<a class="src-link" href="${esc(h.url)}" target="_blank">↗ ${esc((h.title||h.url).slice(0,52))}</a>`).join('')}</div>` : '';
      html+=`<div class="media-cell" style="${lit?'':'opacity:.55'}"><div class="mc-head"><span class="mc-name"><span class="ml-dot ${lit?'lit':''}"></span>${m.rank}. ${esc(m.name)}</span><span class="mc-status ${lit?'hit':''}">${lit?n+' 条':'未报道'}</span></div>${links}</div>`;
    }
    html+=`</div>`;
    updateMediaStatus(d.top_media);
    // 逐条主张的媒体覆盖明细
    if(d.top_media_by_claim&&d.top_media_by_claim.length){
      html+=`<h3>按主张查看报道</h3>`;
      d.top_media_by_claim.forEach((cm,idx)=>{
        const med=cm.media||[];
        const h=med.filter(x=>Number(x.hit_count||0)>0);
        html+=`<div class="ev"><b>主张 ${idx+1}：</b>${esc(cm.claim||'')}<br><span style="color:var(--ok-text)">${h.length} 家媒体报道</span>：${h.map(x=>esc(x.name)).join('、')||'无'}</div>`;
        // 该主张命中的具体来源链接（可点开原文，便于人工审计）
        if(h.length){
          const links=h.flatMap(x=>(x.hits||[])).map(hh=>`<a class="src-link" href="${esc(hh.url||'')}" target="_blank">↗ ${esc((hh.title||hh.url||'').slice(0,48))}</a>`).join('');
          if(links) html+=`<div class="src-list" style="margin:2px 0 6px">${links}</div>`;
        }
      });
    }
  }
  // process history
  if(d.jobs&&d.jobs.length){
    html+=`<h3>任务过程与历史</h3>`;
    for(const j of d.jobs){
      html+=`<div class="ev"><b>${j.kind}</b> · ${j.status}`+
        (j.attempts?` · 执行次数 ${j.attempts}`:'')+
        (j.started_at?` · 开始 ${new Date(j.started_at).toLocaleString()}`:'')+
        (j.finished_at?` · 完成 ${new Date(j.finished_at).toLocaleString()}`:'')+
        (j.error?`<br><span style="color:var(--bad-text)">错误: ${esc(j.error)}</span>`:'')+
        (j.result&&j.result.summary?`<br><b>结果：</b>${esc(j.result.summary)}`:'')+
        `</div>`;
      // progress steps
      if(j.result&&j.result.progress&&j.result.progress.length){
        html+=`<div style="margin:8px 0 4px 12px;border-left:2px solid var(--border);padding-left:12px">`;
        for(const p of j.result.progress){
          html+=`<div style="font-size:11px;color:var(--muted);margin:3px 0">⏱ ${new Date(p.time).toLocaleTimeString()} — ${p.step}</div>`;
        }
        html+=`</div>`;
      }
    }
  }
  html+=`<div style="margin-top:12px"><button class="btn small secondary" onclick="recheckEvent('${d.id}')">重新核查</button></div>`
  // tracking
  html+=`<h3>追踪状态</h3>`;
  if(d.subscriptions&&d.subscriptions.length){
    for(const s of d.subscriptions){
      html+=`<p class="note">${s.active?'🟢 活跃':'⚪ 已停'} · 间隔 ${s.interval_hours}h · 下次 ${s.next_run_at?s.next_run_at:''}</p>`;
    }
  } else {
    html+=`<p class="note">未开启追踪</p>`;
  }
  html+=`<h3>🧠 本条新闻的专属脑图（连线版）</h3>`;
  html+=`${mmToolbar(d.id,false)}
    <button class="mini-btn" onclick="showMindmap('${d.id}')">⛶ 全屏脑图</button>`;
  html+=`<div id="mm-inline-canvas"></div>`;
  html+=`<div class="mm-hint">💡 中心为该新闻，六条彩色连线分别通向主张、证据、媒体、追踪、进度与历史；点击分支可展开/收起。</div>`;
  html+=`<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
    <button class="mini-btn" onclick="showMindmap('${d.id}')">🧠 脑图视图</button>
    <button class="mini-btn track" onclick="showTrackStatus('${d.id}')">📡 追踪状态汇总</button>
    <button class="mini-btn setting" onclick="showTrackSettings('${d.id}')">⚙️ 修改追踪设置</button>
  </div>`;
  html+=`<div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">
    <button class="btn small" onclick="trackEvent('${d.id}','24h')">追踪 24h</button>
    <button class="btn small" onclick="trackEvent('${d.id}','6h')">追踪 6h</button>
    <button class="btn small" onclick="trackEvent('${d.id}','week')">追踪 每周</button>
    <button class="btn small secondary" onclick="untrackEvent('${d.id}')">停止追踪</button>
  </div>`;
  document.getElementById('modalContent').innerHTML=html;
  document.getElementById('modalBg').style.display='flex';
  mmRenderInlineDetail(d);
  // 任务进行中时自动刷新弹窗，实时展示节点与结果。
  // 关键：记录当前视图为 detail，轮询回调仅在仍停留在 detail 视图时才刷新，
  // 否则用户切到追踪状态/设置/脑图后会被强制覆盖回去。
  _modalView='detail'; _modalEventId=id;
  if(latestJob.status==='running'||latestJob.status==='queued'){
    _detailPollId=setTimeout(()=>{
      if(_modalView==='detail' && document.getElementById('modalBg').style.display==='flex') showDetail(id);
    },3000);
  }
}
let _detailPollId=null,_modalView=null,_modalEventId=null;
function stopDetailPoll(){ if(_detailPollId){clearTimeout(_detailPollId);_detailPollId=null;} }
function closeModal(e){
  if(!e||e.target.id==='modalBg'){
    document.getElementById('modalBg').style.display='none';
    stopDetailPoll(); _modalView=null;
  }
}
async function saveTitleFromModal(id){
  const t=document.getElementById('editTitle').value.trim();
  await fetch('/api/events/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:t})});
  alert('已保存'); loadEvents();
}
async function saveTitle(id,el){const t=el.innerText.trim();await fetch('/api/events/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:t})});}
async function submit(){
  const t=document.getElementById('txt').value.trim();
  if(!t){alert('请输入内容');return;}
  const fd=new FormData();fd.append('text',t);
  fd.append('mode',document.getElementById('mode').value);
  fd.append('freq',document.getElementById('freq').value);
  const btn=document.querySelector('button[onclick="submit()"]');
  if(btn){btn.disabled=true;btn.textContent='提交中…';}
  try{
    const r=await fetch('/submit',{method:'POST',body:fd});
    if(!r.ok){ alert('提交失败: HTTP '+r.status); return; }
    const d=await r.json();
    // 立即在任务列表顶部显示该任务（optimistic UI），带"已入队"首节点
    allEvents.unshift({
      id:d.event_id,title:t,status:'queued',job_status:'queued',job_id:d.job_id,
      claims:[],verdicts:[],created_at:new Date().toISOString(),
      job_result:{progress:[{step:'已提交，等待后台接收任务',time:new Date().toISOString()}]}
    });
    filter='all';
    document.querySelectorAll('.tab').forEach((x,i)=>x.classList.toggle('active',i===0));
    renderEvents();
    loadStats();
    // 立即打开详情弹窗，实时展示任务状态与节点进度
    showDetail(d.event_id);
    // 持续轮询直到任务完成（最多 ~2 分钟），并同步列表
    let tries=0;
    const iv=setInterval(async()=>{
      tries++;
      await loadEvents();
      const e=allEvents.find(x=>x.id===d.event_id);
      if(e && (e.job_status==='done'||e.job_status==='failed')){
        clearInterval(iv);
        showDetail(d.event_id);   // 完成后刷新为最终结果
        loadStats();
      }
      if(tries>40) clearInterval(iv);
    },3000);
    setTimeout(()=>clearInterval(iv),130000);
  }catch(e){ console.error('submit',e); alert('提交失败: '+e.message); }
  finally{ if(btn){btn.disabled=false;btn.textContent='开始核查';} }
}
async function trackEvent(id,iv){
  const r=await fetch('/api/track/'+id+'?interval='+iv,{method:'POST'});
  const d=await r.json();
  alert('已开启追踪，间隔 '+d.interval_hours+'h');
  showDetail(id);
}
async function untrackEvent(id){
  await fetch('/api/untrack/'+id,{method:'POST'});
  alert('已停止追踪');
  showDetail(id);
}

// ===== (a) 追踪状态：打开页面汇总显示该新闻的所有更新状态 =====
async function showTrackStatus(id){
  stopDetailPoll(); _modalView='track'; _modalEventId=id;
  const r=await fetch('/api/events/'+id);const d=await r.json();
  if(!d||!d.id){alert('事件不存在');return;}
  const subs=d.subscriptions||[];
  const active=subs.filter(s=>s.active&&!s.paused);
  const notifs=d.notifications||[];
  let html=`<h2>📡 追踪状态汇总 <span class="badge">${d.id.slice(0,8)}</span></h2>`;
  html+=`<div class="sub">${esc(d.title)}</div>`;
  html+=`<div class="track-grid">
    <div class="track-stat"><div class="v">${active.length}</div><div class="l">活跃追踪</div></div>
    <div class="track-stat"><div class="v">${notifs.length}</div><div class="l">累计更新</div></div>
    <div class="track-stat"><div class="v">${active.length?active[0].interval_hours+'h':'—'}</div><div class="l">检查间隔</div></div>
  </div>`;
  if(active.length){
    const s=active[0];
    html+=`<div class="note" style="margin:8px 0">🟢 追踪中 · 下次检查：${s.next_run_at?new Date(s.next_run_at).toLocaleString():'待定'} · 上次检查：${s.last_run_at?new Date(s.last_run_at).toLocaleString():'尚未执行'}</div>`;
  } else {
    html+=`<div class="note" style="margin:8px 0">⚪ 当前未开启追踪</div>`;
  }
  html+=`<h3>所有更新记录（共 ${notifs.length} 条）</h3>`;
  if(notifs.length){
    for(const n of notifs){
      const isBaseline=(n.content_hash||'').startsWith('baseline:');
      const label=n.kind&&n.kind!=='update'?esc(n.kind):(isBaseline?'追踪已启动 · 建立基线':'检测到更新');
      html+=`<div class="upd-item"><b>${isBaseline?'🔹':'🔸'} ${label}</b> <span class="u-time">${n.created_at?new Date(n.created_at).toLocaleString():''}</span><br><span style="color:var(--muted)">指纹 ${esc((n.content_hash||'').replace('baseline:','').slice(0,12))}</span></div>`;
    }
  } else {
    html+=`<div class="note">尚未检测到更新。开启追踪后，系统会按设定间隔复查，一旦发现新证据或结论变化即在此汇总并推送。</div>`;
  }
  html+=`<div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">
    <button class="mini-btn" onclick="showMindmap('${d.id}')" title="以脑图直观查看该新闻的完整核查链路">🧠 脑图视图</button>
    <button class="mini-btn setting" onclick="showTrackSettings('${d.id}')">⚙️ 修改追踪设置</button>
    <button class="mini-btn" onclick="showDetail('${d.id}')">← 返回事件详情</button>
  </div>`;
  document.getElementById('modalContent').innerHTML=html;
  document.getElementById('modalBg').style.display='flex';
}

// ===== (b) 独立设置按钮：修改约定、频率、时间等追踪逻辑 =====
async function showTrackSettings(id){
  stopDetailPoll(); _modalView='settings'; _modalEventId=id;
  const r=await fetch('/api/events/'+id);const d=await r.json();
  if(!d||!d.id){alert('事件不存在');return;}
  const subs=d.subscriptions||[];
  const s=subs.find(x=>x.active)||{interval_hours:24,next_run_at:null,paused:false};
  const hasSub=subs.some(x=>x.active);
  const curIv=s.interval_hours||24;
  let html=`<h2>⚙️ 追踪设置 <span class="badge">${d.id.slice(0,8)}</span></h2>`;
  html+=`<div class="sub">${esc(d.title)}</div>`;
  html+=`<div class="setting-row"><label>检查频率</label>
    <select id="setInterval">
      <option value="6" ${curIv===6?'selected':''}>每 6 小时</option>
      <option value="12" ${curIv===12?'selected':''}>每 12 小时</option>
      <option value="24" ${curIv===24?'selected':''}>每天一次</option>
      <option value="72" ${curIv===72?'selected':''}>每 3 天</option>
      <option value="168" ${curIv===168?'selected':''}>每周一次</option>
    </select></div>`;
  html+=`<div class="setting-row"><label>下次检查时间</label>
    <input type="datetime-local" id="setNext" value="${s.next_run_at?new Date(s.next_run_at).toISOString().slice(0,16):''}"></div>`;
  html+=`<div class="setting-row"><label>暂停追踪</label>
    <input type="checkbox" id="setPaused" ${s.paused?'checked':''}></div>`;
  html+=`<p class="note">修改后点击保存，系统会按新的频率与时间重新安排后续追踪；更新检测与新证据推送逻辑同步生效。</p>`;
  html+=`<div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap">
    <button class="btn small" onclick="saveTrackSettings('${d.id}',${hasSub})">💾 保存设置</button>
    ${hasSub?'':'<button class="btn small secondary" onclick="trackEvent(&quot;'+d.id+'&quot;,&quot;24h&quot;)">先开启追踪</button>'}
    <button class="mini-btn" onclick="showTrackStatus('${d.id}')">← 追踪状态</button>
  </div>`;
  document.getElementById('modalContent').innerHTML=html;
  document.getElementById('modalBg').style.display='flex';
}

__MM_JS__

async function saveTrackSettings(id,hasSub){
  const payload={
    interval_hours:Number(document.getElementById('setInterval').value),
    paused:document.getElementById('setPaused').checked
  };
  const nv=document.getElementById('setNext').value;
  if(nv) payload.next_run_at=new Date(nv).toISOString();
  let r;
  if(hasSub){
    r=await fetch('/api/track/'+id+'/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  } else {
    r=await fetch('/api/track/'+id+'?interval=24h',{method:'POST'});
    if(r.ok){ const sub=await r.json(); if(payload.interval_hours!==24||payload.paused||payload.next_run_at){
      r=await fetch('/api/track/'+id+'/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    }}
  }
  if(r&&r.ok){ alert('追踪设置已保存并生效'); loadEvents(); showTrackStatus(id); }
  else alert('保存失败');
}
async function deleteEvent(id){
  if(!confirm('确认删除该任务及其所有数据？')) return;
  const r=await fetch('/api/events/'+id,{method:'DELETE'});
  if(r.ok){ alert('已删除'); loadEvents(); loadStats(); }
  else alert('删除失败');
}
async function recheckEvent(id){
  const r=await fetch('/api/recheck/'+id,{method:'POST'});
  const d=await r.json();
  alert('已重新提交核查，任务ID: '+d.job_id.slice(0,8));
  loadEvents();
}
loadStats();loadMedia();loadSystem();
loadEvents().then(()=>{
  // 用最近一条已核查事件的媒体结果点亮右侧媒体面板
  const done=(allEvents||[]).find(e=>e.job_result&&e.job_result.top_media);
  if(done) updateMediaStatus(done.job_result.top_media);
  const params=new URLSearchParams(location.search);
  const openId=params.get('open');
  if(openId) showDetail(openId);
});
setInterval(loadEvents,15000);
setInterval(loadStats,15000);
setInterval(loadSystem,30000);
</script>
</body>
</html>"""
    return HTMLResponse(
        html.replace("__USERNAME__", username)
            .replace("__APP_VERSION__", VERSION)
            .replace("__THEME_CSS__", THEME_CSS)
            .replace("__DESIGN_CSS__", DESIGN_CSS)
            .replace("__SHELL_JS__", SHELL_JS)
            .replace("__RELEASE_DATE__", RELEASE_DATE)
            .replace("__CODENAME__", CODENAME)
            .replace("__TOP_MEDIA_COUNT__", str(len(TOP_MEDIA)))
            .replace("__MM_CSS__", MM_CSS)
            .replace("__MM_JS__", MM_JS)
    )