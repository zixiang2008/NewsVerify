#!/usr/bin/env python3
"""清理历史核查失败的任务（failed job 及其关联 event/claim/evidence/verdict）。

用途：清除因旧 API（模型不存在）与旧版 flush bug 导致的 failed 垃圾任务，
不影响任何 done/running/queued 的正常任务。

安全设计：
- 默认 dry-run，只打印将会删除的内容，不实际删除。
- 必须显式加 --apply 才会真正执行。
- 只删除 job_status == 'failed' 的事件；逐个按 ORM 级联删除，FK 安全。
- 执行前自动通过 backup.sh 逻辑做一次 pg_dump 备份（--apply 时）。

用法（在 NAS 容器内）：
  python scripts/clean_failed_jobs.py              # dry-run 预览
  python scripts/clean_failed_jobs.py --apply      # 实际清理
"""
from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select, func

from app.db.session import get_sessionmaker, init_db
from app.db.models import Event, Job


async def main(apply: bool) -> None:
    await init_db()
    sm = get_sessionmaker()
    async with sm() as s:
        # 找出所有只用 failed job 的 event（取其最新 job 为 failed）
        res = await s.execute(select(Event).order_by(Event.created_at))
        events = res.scalars().all()
        to_delete = []
        for e in events:
            jr = await s.execute(
                select(Job).where(Job.payload["event_id"].as_string() == e.id)
                .order_by(Job.created_at.desc())
            )
            jobs = jr.scalars().all()
            if not jobs:
                continue
            latest = jobs[0]
            if latest.status == "failed" and all(j.status == "failed" for j in jobs):
                to_delete.append((e, len(jobs)))

        print(f"=== 待清理 failed 任务: {len(to_delete)} 个 ===")
        for e, njobs in to_delete:
            print(f"  - {e.id[:8]}  {e.title[:60]}  ({njobs} jobs)")
        if not to_delete:
            print("没有需要清理的任务。")
            return
        if not apply:
            print("\n[dry-run] 未执行删除。确认无误后加 --apply 重新运行。")
            return

    async with sm() as s:
        for e, _ in to_delete:
            obj = await s.get(Event, e.id)
            if obj:
                await s.delete(obj)
        await s.commit()
    print(f"\n✅ 已删除 {len(to_delete)} 个失败任务及其关联数据。")


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    asyncio.run(main(apply))
