from __future__ import annotations

import json
import uuid

from aiogram import Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.core.config import get_settings
from app.core.security import validate_url
from app.db.models import Event, Job, Claim
from app.db.session import get_sessionmaker

router = Router()


def _is_allowed(user_id: int) -> bool:
    return user_id in get_settings().allowed_user_ids()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("未授权。")
        return
    await message.answer(
        "NewsVerify 新闻事实核查助手。\n"
        "直接发送新闻文字、链接、转发内容或图片。\n"
        "命令：/help /check /deep /track /untrack /status /history /privacy"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return
    await message.answer(
        "/check <文本或URL> 快速核查\n"
        "/deep <文本或URL> 深度核查\n"
        "/track <事件ID> [6h|24h|week] 开启追踪\n"
        "/untrack <事件ID> 停止追踪\n"
        "/status 任务状态\n"
        "/history 历史记录\n"
        "/privacy 隐私说明"
    )


@router.message(Command("privacy"))
async def cmd_privacy(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return
    await message.answer(
        "隐私说明：消息内容用于核查与追踪；证据摘要与哈希存储；原始网页内容按版权/隐私策略限制存储。"
        "数据保留期按配置（默认90天）。发送 /untrack 可停止追踪。"
    )


async def _enqueue_check(message: Message, deep: bool = False) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("未授权，无法触发核查。")
        return
    text = message.text or ""
    # strip command
    if text.startswith("/"):
        parts = text.split(maxsplit=1)
        text = parts[1] if len(parts) > 1 else ""
    # collect urls from entities
    urls = []
    if message.entities:
        for e in message.entities:
            if e.type == "url":
                urls.append(message.text[e.offset:e.offset + e.length])
            elif e.type == "text_link":
                urls.append(e.url)
    payload_text = text
    if message.caption:
        payload_text = (payload_text + "\n" + message.caption).strip()

    sm = get_sessionmaker()
    async with sm() as session:
        event = Event(title=(payload_text[:120] or "news"), status="queued")
        session.add(event)
        await session.flush()
        job = Job(
            kind="deep_check" if deep else "check",
            status="queued",
            payload={
                "event_id": event.id,
                "text": payload_text,
                "urls": urls,
                "deep": deep,
                "chat_id": message.chat.id,
                "user_id": message.from_user.id,
            },
            user_id=message.from_user.id,
            chat_id=message.chat.id,
        )
        session.add(job)
        await session.commit()
        event_id = event.id
        job_id = job.id

    await message.answer(f"已收到，正在核查…\n任务ID: {job_id}\n事件ID: {event_id}")


@router.message(Command("check"))
async def cmd_check(message: Message) -> None:
    await _enqueue_check(message, deep=False)


@router.message(Command("deep"))
async def cmd_deep(message: Message) -> None:
    await _enqueue_check(message, deep=True)


@router.message(F.text)
async def handle_text(message: Message) -> None:
    # Treat any plain text as a check request
    if not _is_allowed(message.from_user.id):
        await message.answer("未授权。")
        return
    if message.text.startswith("/"):
        return
    await _enqueue_check(message, deep=False)


@router.message(F.photo)
async def handle_photo(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        await message.answer("未授权。")
        return
    await message.answer("图片已收到；MVP 暂不支持 OCR，请转发文字或链接。")


@router.callback_query(F.data.startswith("ev:"))
async def cb_evidence(cb: CallbackQuery) -> None:
    event_id = cb.data.split(":", 1)[1]
    await cb.answer("证据查看功能开发中。", show_alert=False)


@router.callback_query(F.data.startswith("deep:"))
async def cb_deep(cb: CallbackQuery) -> None:
    event_id = cb.data.split(":", 1)[1]
    await cb.answer("已请求深度核查。", show_alert=False)


@router.callback_query(F.data.startswith("track:"))
async def cb_track(cb: CallbackQuery) -> None:
    event_id = cb.data.split(":", 1)[1]
    await cb.answer("请使用 /track " + event_id, show_alert=True)


@router.callback_query(F.data.startswith("recheck:"))
async def cb_recheck(cb: CallbackQuery) -> None:
    event_id = cb.data.split(":", 1)[1]
    await cb.answer("请使用 /check 重新提交。", show_alert=True)


@router.callback_query(F.data.startswith("untrack:"))
async def cb_untrack(cb: CallbackQuery) -> None:
    event_id = cb.data.split(":", 1)[1]
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select, update
        from app.db.models import Subscription
        await session.execute(
            update(Subscription).where(Subscription.event_id == event_id).values(active=False, paused=True)
        )
        await session.commit()
    await cb.answer("已停止追踪。", show_alert=False)


@router.message(Command("track"))
async def cmd_track(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("用法: /track <事件ID> [6h|24h|week]")
        return
    event_id = parts[1]
    interval = get_settings().tracking_default_interval_hours
    if len(parts) >= 3:
        arg = parts[2].lower()
        if arg in ("6h", "fast"):
            interval = get_settings().tracking_fast_interval_hours
        elif arg in ("week", "weekly"):
            interval = get_settings().tracking_weekly_interval_hours
    sm = get_sessionmaker()
    async with sm() as session:
        from app.db.models import Subscription
        from datetime import datetime, timezone, timedelta
        sub = Subscription(
            event_id=event_id,
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            interval_hours=interval,
            next_run_at=datetime.now(timezone.utc) + timedelta(hours=interval),
        )
        session.add(sub)
        await session.commit()
    await message.answer(f"已开启追踪：事件 {event_id}，间隔 {interval}h。")


@router.message(Command("untrack"))
async def cmd_untrack(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("用法: /untrack <事件ID>")
        return
    event_id = parts[1]
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import update
        from app.db.models import Subscription
        await session.execute(
            update(Subscription).where(Subscription.event_id == event_id).values(active=False, paused=True)
        )
        await session.commit()
    await message.answer(f"已停止追踪事件 {event_id}。")


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select, func
        from app.db.models import Job
        res = await session.execute(select(func.count()).select_from(Job).where(Job.user_id == message.from_user.id))
        total = res.scalar() or 0
        res2 = await session.execute(select(Job).where(Job.user_id == message.from_user.id).order_by(Job.created_at.desc()).limit(5))
        jobs = res2.scalars().all()
    lines = [f"任务总数: {total}"]
    for j in jobs:
        lines.append(f"- {j.id[:8]} {j.kind} {j.status}")
    await message.answer("\n".join(lines))


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    if not _is_allowed(message.from_user.id):
        return
    sm = get_sessionmaker()
    async with sm() as session:
        from sqlalchemy import select
        from app.db.models import Event
        res = await session.execute(select(Event).order_by(Event.created_at.desc()).limit(10))
        events = res.scalars().all()
    lines = ["最近事件:"]
    for e in events:
        lines.append(f"- {e.id[:8]} {e.title[:60]}")
    await message.answer("\n".join(lines))


def register(dp: Dispatcher) -> None:
    dp.include_router(router)