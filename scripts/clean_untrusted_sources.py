#!/usr/bin/env python3
"""Remove historical sources that fail NewsVerify's trusted-source whitelist.

Baidu Baike/Wenku, QQ, Sohu, Huxiu, Wikipedia and similar aggregators used to
enter the evidence pool through search results. This script removes their
``Source`` rows and the linked ``Evidence`` rows, without touching claims,
verdicts, events, jobs or subscriptions.

Safety:
  - Dry-run by default; ``--apply`` is required for actual deletion.
  - Only rows rejected by ``classify_source()`` are removed.
  - Run ``scripts/backup.sh`` (pg_dump) before applying on production.

Usage inside the container:
  python scripts/clean_untrusted_sources.py
  python scripts/clean_untrusted_sources.py --apply
"""
from __future__ import annotations

import asyncio
import sys

from sqlalchemy import delete, select

from app.db.models import Evidence, Source
from app.db.session import get_sessionmaker, init_db
from app.verification.source_policy import classify_source


async def main(apply: bool) -> None:
    await init_db()
    sm = get_sessionmaker()
    async with sm() as s:
        sources = (await s.execute(select(Source))).scalars().all()
        rejected = []
        for src in sources:
            category, host = classify_source(src.url)
            if category is None:
                ev_count = (await s.execute(
                    select(Evidence.id).where(Evidence.source_id == src.id)
                )).scalars().all()
                rejected.append((src, host, len(ev_count)))

        print(f"=== 未通过可信来源白名单的历史来源: {len(rejected)} / {len(sources)} ===")
        for src, host, n in rejected:
            print(f"  - {host or '(invalid url)'}  evidence={n}  {src.url[:100]}")
        if not rejected:
            print("没有需要清理的来源。")
            return
        if not apply:
            print("\n[dry-run] 未删除任何数据。确认后加 --apply 重新运行。")
            return

        total_ev = 0
        for src, _, n in rejected:
            await s.execute(delete(Evidence).where(Evidence.source_id == src.id))
            await s.delete(src)
            total_ev += n
        await s.commit()
        print(f"\n已删除 {len(rejected)} 个来源、{total_ev} 条关联证据。")


if __name__ == "__main__":
    asyncio.run(main("--apply" in sys.argv))
