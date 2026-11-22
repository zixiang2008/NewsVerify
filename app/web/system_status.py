"""系统运行状态采集：资源消耗 + 外部 API 在线探测。

仅使用 Python 标准库，避免引入 psutil 等新依赖导致容器构建失败。
支持 Linux (/proc，容器实际环境) 与 macOS (sysctl) 的 fallback。
"""
from __future__ import annotations

import asyncio
import os
import resource
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

from app.core.config import get_settings


def _read_proc_stat() -> Dict[str, float]:
    """读取 /proc 得到 CPU 使用率和内存信息（Linux 容器）。"""
    result: Dict[str, float] = {}
    try:
        with open("/proc/stat", "r", encoding="utf-8") as f:
            line = f.readline().split()
        # user nice system idle iowait irq softirq steal guest guest_nice
        vals = [float(x) for x in line[1:]]
        idle = vals[3] + (vals[4] if len(vals) > 4 else 0)
        total = sum(vals)
        result["cpu_idle"] = idle
        result["cpu_total"] = total
    except Exception:
        pass
    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as f:
            mem = {}
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    mem[parts[0]] = float(parts[1].strip().split()[0])
        total_kb = mem.get("MemTotal", 0)
        avail_kb = mem.get("MemAvailable", mem.get("MemFree", 0))
        result["mem_total_kb"] = total_kb
        result["mem_avail_kb"] = avail_kb
        result["mem_used_pct"] = ((total_kb - avail_kb) / total_kb * 100) if total_kb else 0.0
    except Exception:
        pass
    return result


_cpu_prev: Dict[str, float] = {}
_start_time = time.time()


def _cpu_percent() -> float | None:
    global _cpu_prev
    cur = _read_proc_stat()
    if "cpu_total" not in cur or "cpu_idle" not in cur:
        # 非 Linux（如 macOS 开发环境）用 os.getloadavg 近似单核负载百分比
        try:
            load1 = os.getloadavg()[0]
            cores = os.cpu_count() or 1
            return round(min(100.0, load1 / cores * 100), 1)
        except Exception:
            return None
    if _cpu_prev:
        dt = cur["cpu_total"] - _cpu_prev.get("cpu_total", 0)
        di = cur["cpu_idle"] - _cpu_prev.get("cpu_idle", 0)
        if dt > 0:
            pct = (1.0 - di / dt) * 100
            _cpu_prev = cur
            return round(max(0.0, min(100.0, pct)), 1)
    _cpu_prev = cur
    return None


def _resource_usage() -> Dict[str, Any]:
    usage: Dict[str, Any] = {}
    try:
        rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Linux 上 ru_maxrss 单位是 KB，macOS 上是 bytes
        if sys.platform == "darwin":
            rss_kb = rss_kb / 1024
        usage["process_rss_mb"] = round(rss_kb / 1024, 1)
    except Exception:
        pass
    try:
        usage["open_fds"] = len(os.listdir("/proc/self/fd"))
    except Exception:
        pass
    return usage


def _disk_usage() -> Dict[str, Any]:
    try:
        st = os.statvfs("/")
        total = st.f_blocks * st.f_frsize
        free = st.f_bfree * st.f_frsize
        used_pct = ((total - free) / total * 100) if total else 0.0
        return {
            "total_gb": round(total / 1024 ** 3, 1),
            "free_gb": round(free / 1024 ** 3, 1),
            "used_pct": round(used_pct, 1),
        }
    except Exception:
        return {}


async def _probe_api(name: str, url: str, key: str = "", timeout: float = 6.0) -> Dict[str, Any]:
    """探测单个外部 API 的 /models 端点，记录响应延迟。"""
    started = time.perf_counter()
    result: Dict[str, Any] = {
        "name": name,
        "url": url,
        "online": False,
        "latency_ms": None,
        "detail": "",
    }
    check_url = url.rstrip("/") + "/models"
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(check_url, headers=headers)
        elapsed = (time.perf_counter() - started) * 1000
        result["latency_ms"] = round(elapsed, 0)
        if resp.status_code < 400:
            result["online"] = True
            try:
                data = resp.json()
                models = data.get("data", []) if isinstance(data, dict) else []
                result["detail"] = f"HTTP {resp.status_code} · {len(models)} 个模型可用" if models else f"HTTP {resp.status_code} · 可达"
            except Exception:
                result["detail"] = f"HTTP {resp.status_code} · 可达"
        else:
            result["detail"] = f"HTTP {resp.status_code}"
    except httpx.TimeoutException:
        result["latency_ms"] = round((time.perf_counter() - started) * 1000, 0)
        result["detail"] = "连接超时"
    except Exception as e:  # noqa: BLE001
        result["latency_ms"] = round((time.perf_counter() - started) * 1000, 0)
        result["detail"] = f"连接失败: {type(e).__name__}"
    return result


async def _probe_search_health(name: str, health: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a search health probe result into the same shape as API probes."""
    ok = bool(health.get("healthy"))
    return {
        "name": name,
        "url": "query-diversity probe",
        "online": ok,
        "latency_ms": None,
        "detail": (
            "查询响应正常且随查询变化"
            if ok else
            f"检索层降级：{health.get('detail', '返回固定或不相关结果')} "
            f"(sample {health.get('query_results', 0)}/{health.get('control_results', 0)})"
        ),
    }


async def get_system_status() -> Dict[str, Any]:
    """汇总系统资源与外部 API 在线状态。"""
    s = get_settings()
    endpoints = s.llm_endpoints()

    # 并行探测所有外部 API 与搜索
    probes: List[asyncio.Task] = []
    for i, url in enumerate(endpoints):
        label = "LLM 主 API" if i == 0 else f"LLM 备用 API {i}"
        probes.append(asyncio.create_task(_probe_api(label, url, s.llm_api_key)))
    # 搜索层健康探测：不再只 ping 首页（首页 200 无法发现"返回固定无关结果"
    # 这种半故障）。用两个语义不同的查询验证上游是否真的会随查询变化。
    search_name = f"搜索 ({s.search_provider})"
    search_health: Dict[str, Any] = {"healthy": None, "detail": "未探测"}
    try:
        from app.verification.search import search_health_probe
        search_health = await asyncio.wait_for(search_health_probe(), timeout=25)
        probes.append(asyncio.create_task(_probe_search_health(search_name, search_health)))
    except Exception as exc:
        search_health = {"healthy": False, "detail": f"探测失败: {type(exc).__name__}"}
        probes.append(asyncio.create_task(_probe_search_health(search_name, search_health)))

    api_results = await asyncio.gather(*probes, return_exceptions=True)
    apis: List[Dict[str, Any]] = []
    for r in api_results:
        if isinstance(r, Exception):
            apis.append({"name": "未知", "url": "", "online": False, "latency_ms": None, "detail": str(r)})
        else:
            apis.append(r)

    # LLM 当前生效的端点（熔断最少的）
    try:
        from app.verification.llm import LLMClient
        active_llm = LLMClient.last_used_endpoint()
        endpoint_failures = LLMClient.endpoint_health()
    except Exception:
        active_llm = endpoints[0] if endpoints else ""
        endpoint_failures = {}

    cpu_pct = _cpu_percent()
    proc = _resource_usage()
    disk = _disk_usage()
    mem = _read_proc_stat()

    # 当前进程数（Linux）
    try:
        process_count = len([p for p in os.listdir("/proc") if p.isdigit()])
    except Exception:
        process_count = None

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server_time": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "uptime_seconds": int(time.time() - _start_time),
        "system": {
            "platform": sys.platform,
            "python": sys.version.split()[0],
            "cpu_percent": cpu_pct,
            "memory_used_pct": round(mem.get("mem_used_pct", 0.0), 1),
            "memory_total_mb": round(mem.get("mem_total_kb", 0) / 1024, 0),
            "disk": disk,
            "process_rss_mb": proc.get("process_rss_mb"),
            "open_fds": proc.get("open_fds"),
            "process_count": process_count,
        },
        "apis": apis,
        "search_health": search_health,
        "active_llm_endpoint": active_llm,
        "endpoint_failures": endpoint_failures,
        "config": {
            "llm_model": s.llm_model,
            "judge_model": s.llm_judge_model,
            "search_provider": s.search_provider,
        },
    }
