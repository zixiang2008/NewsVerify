"""Account authentication for NewsVerify.

Session cookie = ``username|role|HMAC`` so the middleware stays stateless and
offline-safe.  PINs are one-way hashed with a per-account salt (the username),
never stored in clear text.  Two built-in super administrators are seeded on
every startup: caishen/1314 and kayla/0720.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import os
import re
import secrets
from typing import Any

from sqlalchemy import select

SUPER_ADMINS = [
    {"username": "caishen", "pin": "1314", "display_name": "Caishen · 超级管理员"},
    {"username": "kayla", "pin": "0720", "display_name": "Kayla · 超级管理员"},
]
AUTH_SECRET = os.getenv("AUTH_SECRET", "newsverify-local-auth-v1")
USERNAME_RE = re.compile(r"^[\w\u4e00-\u9fff-]{2,32}$", re.UNICODE)
PIN_RE = re.compile(r"^\d{4}$")
CODE_RE = re.compile(r"^\d{6}$")


def hash_pin(username: str, pin: str) -> str:
    return hashlib.sha256(f"nv-auth-v1:{username.strip().lower()}:{pin}".encode()).hexdigest()


def verify_pin(username: str, pin: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_pin(username, pin), stored_hash or "")


def _sign(payload: str) -> str:
    return hmac.new(AUTH_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]


def make_session(username: str, role: str) -> str:
    payload = f"{username}|{role}"
    return f"{payload}|{_sign(payload)}"


def parse_session(token: str | None) -> dict[str, str] | None:
    if not token:
        return None
    parts = token.split("|")
    if len(parts) != 3:
        return None
    username, role, sig = parts
    if not hmac.compare_digest(_sign(f"{username}|{role}"), sig):
        return None
    return {"username": username, "role": role}


async def seed_super_admins(sessionmaker) -> None:
    """Idempotently (re)create the two built-in administrator accounts."""
    from app.db.models import User

    async with sessionmaker() as session:
        for item in SUPER_ADMINS:
            username = item["username"]
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            if user is None:
                user = User(username=username, display_name=item["display_name"], role="super_admin")
                session.add(user)
            user.pin_hash = hash_pin(username, item["pin"])
            user.display_name = item["display_name"]
            user.role = "super_admin"
            user.active = True
        await session.commit()


async def authenticate(sessionmaker, username: str, pin: str) -> dict[str, Any] | None:
    from app.db.models import User

    username = (username or "").strip().lower()
    if not USERNAME_RE.match(username) or not PIN_RE.match(pin or ""):
        return None
    async with sessionmaker() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if not user or not user.active or not verify_pin(username, pin, user.pin_hash):
            return None
        user.last_login_at = dt.datetime.now(dt.timezone.utc)
        await session.commit()
        return {"username": user.username, "role": user.role, "display_name": user.display_name}


async def register_with_invite(
    sessionmaker, username: str, pin: str, code: str
) -> tuple[bool, str, dict[str, str] | None]:
    """Create a normal account using one invitation slot. Returns (ok, message, user)."""
    from app.db.models import InviteCode, User

    username = (username or "").strip().lower()
    code = (code or "").strip()
    if not USERNAME_RE.match(username):
        return False, "用户名需为 2–32 位字母、数字、下划线或汉字", None
    if not PIN_RE.match(pin or ""):
        return False, "PIN 码必须是 4 位数字", None
    if not CODE_RE.match(code):
        return False, "邀请码必须是 6 位数字", None

    async with sessionmaker() as session:
        existing = await session.execute(select(User).where(User.username == username))
        if existing.scalars().first():
            return False, "该用户名已被注册，请换一个", None

        result = await session.execute(select(InviteCode).where(InviteCode.code == code))
        invite = result.scalars().first()
        if not invite or not invite.active:
            return False, "邀请码无效或已被撤销", None
        now = dt.datetime.now(dt.timezone.utc)
        if invite.expires_at:
            expiry = invite.expires_at
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=dt.timezone.utc)
            if expiry < now:
                return False, "邀请码已过期", None
        if invite.used_count >= invite.max_uses:
            return False, "邀请码使用次数已用完", None

        # Atomic decrement: concurrent registrations cannot over-use one code.
        from sqlalchemy import update
        claimed = await session.execute(
            update(InviteCode)
            .where(InviteCode.id == invite.id, InviteCode.used_count < InviteCode.max_uses)
            .values(used_count=InviteCode.used_count + 1)
        )
        if claimed.rowcount != 1:
            return False, "邀请码使用次数已用完，请换一个", None

        user = User(
            username=username,
            pin_hash=hash_pin(username, pin),
            display_name=username,
            role=invite.role or "user",
            invited_by=invite.created_by or "",
        )
        session.add(user)
        await session.commit()
        return True, "注册成功，请使用用户名与 PIN 登录", {
            "username": username, "role": user.role, "display_name": user.display_name
        }


def generate_codes(count: int, role: str, note: str, created_by: str,
                   max_uses: int = 1, expires_days: int | None = None) -> dict[str, Any]:
    """Build a batch of unique six-digit codes (caller persists them)."""
    batch = secrets.token_hex(4)
    codes: list[str] = []
    seen: set[str] = set()
    while len(codes) < max(1, min(200, int(count))):
        c = f"{secrets.randbelow(1000000):06d}"
        if c in seen:
            continue
        seen.add(c)
        codes.append(c)
    expires = None
    if expires_days:
        expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=int(expires_days))
    return {
        "batch": batch,
        "codes": codes,
        "role": role if role in ("user", "super_admin") else "user",
        "note": (note or "").strip()[:200],
        "created_by": created_by,
        "max_uses": max(1, min(100, int(max_uses))),
        "expires_at": expires,
    }
