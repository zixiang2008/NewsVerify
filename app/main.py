from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import init_db


async def run_bot() -> None:
    from aiogram import Bot, Dispatcher
    from app.bot.handlers import register
    settings = get_settings()
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    register(dp)
    await dp.start_polling(bot)


async def run_worker() -> None:
    from app.worker import run_worker as _rw
    await _rw()


async def run_web() -> None:
    import uvicorn
    from app.web.app import app
    settings = get_settings()
    config = uvicorn.Config(app, host="0.0.0.0", port=8095, log_level=settings.log_level.lower())
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    await init_db()
    mode = (settings.app_mode or "bot").lower()
    if mode == "worker":
        await run_worker()
    elif mode == "web":
        await run_web()
    elif mode == "all":
        await asyncio.gather(run_bot(), run_web())
    else:
        await run_bot()


if __name__ == "__main__":
    asyncio.run(main())