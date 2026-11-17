from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def check_keyboard(event_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="查看证据", callback_data=f"ev:{event_id}"),
            InlineKeyboardButton(text="深度核查", callback_data=f"deep:{event_id}"),
        ],
        [
            InlineKeyboardButton(text="追踪此事件", callback_data=f"track:{event_id}"),
            InlineKeyboardButton(text="重新核查", callback_data=f"recheck:{event_id}"),
        ],
    ])


def track_keyboard(event_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="停止追踪", callback_data=f"untrack:{event_id}")],
    ])