from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.core.config import get_settings


class LLMClient:
    """OpenAI 兼容客户端，支持主/备 API 自动切换。

    - 主 API (LLM_BASE_URL) 不可用时自动切到备用 (LLM_BASE_URL_FALLBACK)。
    - 端点级熔断：某端点连续失败后在本进程内暂时跳过，避免每次都等待超时。
    - 记录最近一次实际使用的端点与延迟，供系统状态面板展示。
    """

    # 类级熔断状态，进程内共享
    _endpoint_failures: Dict[str, int] = {}
    _MAX_ENDPOINT_FAILURES = 2

    def __init__(self) -> None:
        s = get_settings()
        self.model = s.llm_model
        self.judge_model = s.llm_judge_model
        self.timeout = s.llm_timeout_seconds
        self.api_key = s.llm_api_key or "sk-noop"
        self.endpoints: List[str] = s.llm_endpoints()
        self._clients: Dict[str, AsyncOpenAI] = {}
        for url in self.endpoints:
            # max_retries=0：重试由本类的主备切换统一负责，避免 openai 内部
            # 再叠加 N 次 60s 超时导致单个任务卡几分钟。
            self._clients[url] = AsyncOpenAI(
                base_url=url, api_key=self.api_key, timeout=self.timeout, max_retries=0
            )

    def _ordered_endpoints(self) -> List[str]:
        """把熔断中的端点排到后面。"""
        return sorted(
            self.endpoints,
            key=lambda u: LLMClient._endpoint_failures.get(u, 0),
        )

    def _mark_failure(self, url: str) -> None:
        LLMClient._endpoint_failures[url] = LLMClient._endpoint_failures.get(url, 0) + 1

    def _mark_success(self, url: str) -> None:
        LLMClient._endpoint_failures[url] = 0

    @classmethod
    def last_used_endpoint(cls) -> str:
        s = get_settings()
        eps = s.llm_endpoints()
        if not eps:
            return ""
        return min(eps, key=lambda u: cls._endpoint_failures.get(u, 0))

    @classmethod
    def endpoint_health(cls) -> Dict[str, int]:
        return {u: cls._endpoint_failures.get(u, 0) for u in get_settings().llm_endpoints()}

    async def _chat(self, system: str, user: str, model: str, temperature: float,
                    json_mode: bool) -> tuple[str, str, float]:
        """依次尝试各端点，返回 (content, used_endpoint, elapsed_seconds)。"""
        import asyncio
        import time

        last_error: Optional[Exception] = None
        for url in self._ordered_endpoints():
            client = self._clients[url]
            started = time.perf_counter()
            try:
                kwargs: Dict[str, Any] = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                }
                if json_mode:
                    kwargs["response_format"] = {"type": "json_object"}
                resp = await client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content or ""
                elapsed = time.perf_counter() - started
                self._mark_success(url)
                return content, url, elapsed
            except Exception as e:  # noqa: BLE001 - 需要在端点级别统一容错
                last_error = e
                self._mark_failure(url)
                # 端点失败，尝试下一个；短暂让出事件循环
                await asyncio.sleep(0)
        raise RuntimeError(f"all LLM endpoints failed: {last_error}")

    async def chat_json(self, system: str, user: str, model: Optional[str] = None,
                        temperature: float = 0.2) -> Dict[str, Any]:
        m = model or self.model
        content, _url, _elapsed = await self._chat(system, user, m, temperature, True)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试从文本中提取 JSON
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(content[start:end + 1])
                except Exception:
                    pass
            return {"_raw": content, "_parse_error": True}

    async def chat_text(self, system: str, user: str, model: Optional[str] = None,
                        temperature: float = 0.3) -> str:
        m = model or self.model
        content, _url, _elapsed = await self._chat(system, user, m, temperature, False)
        return content
