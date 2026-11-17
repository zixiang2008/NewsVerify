"""Persistent, masked credential store for instant-messaging channels.

Credentials saved from the admin wizard live in the ``im_channel_configs``
table instead of the ``.env`` file, so connecting a platform is a pure web
action: fill a form, save, test — no code editing, no container restart.

All read paths return *masked* values; only ``get_raw`` (server-side, for
actually sending messages) exposes the full secret.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IMChannelConfig
from app.db.session import get_sessionmaker


def mask(value: Any) -> str:
    s = str(value or "")
    if not s:
        return ""
    if len(s) <= 8:
        return "••••"
    return s[:4] + "••••" + s[-4:]


def mask_credentials(creds: Dict[str, Any], secret_names: set[str]) -> Dict[str, str]:
    return {k: ("••••" if k in secret_names and str(v or "") else mask(v)) for k, v in creds.items()}


def merge_credentials(old: Dict[str, Any], new: Dict[str, Any], secret_names: set[str]) -> Dict[str, Any]:
    """Merge wizard submission into stored credentials.

    Empty fields, and values that are the mask placeholder, keep the old value.
    This lets the UI show masked secrets without ever echoing them back.
    """
    out = dict(old or {})
    for k, v in (new or {}).items():
        s = str(v or "").strip()
        if not s or s == "••••":
            continue
        out[k] = s
    return out


async def _get_row(session: AsyncSession, key: str) -> IMChannelConfig | None:
    res = await session.execute(select(IMChannelConfig).where(IMChannelConfig.key == key))
    return res.scalar_one_or_none()


async def get_record(key: str) -> Dict[str, Any] | None:
    sm = get_sessionmaker()
    async with sm() as session:
        row = await _get_row(session, key)
        if not row:
            return None
        return {
            "key": row.key,
            "credentials": dict(row.credentials or {}),
            "enabled": row.enabled,
            "bound_chat_id": row.bound_chat_id,
            "last_test_ok": row.last_test_ok,
            "last_test_at": row.last_test_at.isoformat() if row.last_test_at else "",
            "last_error": row.last_error,
        }


async def get_raw_credentials(key: str) -> Dict[str, Any]:
    rec = await get_record(key)
    return rec["credentials"] if rec else {}


async def load_all_raw() -> Dict[str, Dict[str, Any]]:
    sm = get_sessionmaker()
    out: Dict[str, Dict[str, Any]] = {}
    async with sm() as session:
        res = await session.execute(select(IMChannelConfig))
        for row in res.scalars().all():
            out[row.key] = dict(row.credentials or {})
    return out


async def save_record(
    key: str,
    credentials: Dict[str, Any],
    *,
    enabled: bool = True,
    bound_chat_id: str | None = None,
) -> Dict[str, Any]:
    sm = get_sessionmaker()
    async with sm() as session:
        row = await _get_row(session, key)
        if not row:
            row = IMChannelConfig(key=key, credentials=dict(credentials))
            session.add(row)
        else:
            row.credentials = dict(credentials)
            row.enabled = enabled
            if bound_chat_id is not None:
                row.bound_chat_id = bound_chat_id
            row.updated_at = dt.datetime.now(dt.timezone.utc)
        await session.commit()
    return await get_record(key) or {"key": key, "credentials": dict(credentials)}


async def set_bound_chat(key: str, chat_id: str) -> None:
    sm = get_sessionmaker()
    async with sm() as session:
        row = await _get_row(session, key)
        if row:
            row.bound_chat_id = str(chat_id)
            row.updated_at = dt.datetime.now(dt.timezone.utc)
            await session.commit()


async def set_test_result(key: str, ok: bool, error: str = "") -> None:
    sm = get_sessionmaker()
    async with sm() as session:
        row = await _get_row(session, key)
        if row:
            row.last_test_ok = bool(ok)
            row.last_test_at = dt.datetime.now(dt.timezone.utc)
            row.last_error = (error or "")[:500]
            await session.commit()


async def delete_record(key: str) -> bool:
    sm = get_sessionmaker()
    async with sm() as session:
        row = await _get_row(session, key)
        if not row:
            return False
        await session.delete(row)
        await session.commit()
        return True
