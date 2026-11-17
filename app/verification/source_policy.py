"""Trusted source policy for NewsVerify.

Only globally credible fact-checking sources, established news organisations
and well-known search-engine entry points are allowed to enter the evidence
pool. Aggregators, user-generated encyclopedias and regional content farms
(e.g. Baidu, QQ, Sohu, Huxiu, Wikipedia) are explicitly rejected.

The policy is a strict whitelist with an explicit deny-list for fast rejection.
Every decision is based on the registrable domain from the URL host, so
subdomains such as ``baike.baidu.com`` or ``cn.nytimes.com`` are handled
correctly.

Reference points:
  - Media Bias/Fact Check (MBFC): factual reporting ratings
  - Reuters Institute Digital News Report: public trust in news brands
  - Google Fact Check Tools: professional fact-check publishers
"""

from __future__ import annotations

from typing import Dict, List, Tuple
from urllib.parse import urlparse

from app.verification.top_media import TOP_MEDIA

# ---------------------------------------------------------------------------
# Tier 1: the 30 media outlets used by the cross-check panel.
# Aliases cover their well-known regional / fact-check sub-properties.
# ---------------------------------------------------------------------------
MEDIA_ALIASES: Dict[str, List[str]] = {
    "bbc.com": ["bbc.com", "bbc.co.uk"],
    "nytimes.com": ["nytimes.com", "cn.nytimes.com"],
    "reuters.com": ["reuters.com", "link.reuters.com"],
    "afp.com": ["afp.com", "factcheck.afp.com", "factcheck.afp.org"],
    "apnews.com": ["apnews.com"],
    "thehindu.com": ["thehindu.com", "hindustantimes.com"],
}

MEDIA_DOMAINS: set[str] = set()
for _m in TOP_MEDIA:
    MEDIA_DOMAINS.add(_m["domain"])
    MEDIA_DOMAINS.update(MEDIA_ALIASES.get(_m["domain"], []))

# ---------------------------------------------------------------------------
# Tier 2: dedicated professional fact-checking organisations that are not
# already part of the Top 30 panel.
# ---------------------------------------------------------------------------
FACTCHECK_DOMAINS: set[str] = {
    "leadstories.com",
    "climatefeedback.org",
    "healthfeedback.org",
    "sciencefeedback.co",
    "checkyourfact.com",
    "aap.com.au",
    "rmitfactlab.org",
    "maldita.es",
}

# ---------------------------------------------------------------------------
# Tier 3: globally recognised search-engine entry points. These are allowed
# as traceable retrieval entry points, not as editorial evidence by themselves.
# ---------------------------------------------------------------------------
SEARCH_ENGINE_DOMAINS: set[str] = {
    "google.com",
    "bing.com",
    "duckduckgo.com",
    "yahoo.com",
    "brave.com",
    "startpage.com",
    "searx.be",
    "mojeek.com",
}

# ---------------------------------------------------------------------------
# Tier 4: authoritative primary sources (government / intergovernmental /
# scholarly institutions) that may serve as reviewable reference material.
# ---------------------------------------------------------------------------
AUTHORITY_DOMAINS: set[str] = {
    "nasa.gov",
    "noaa.gov",
    "nist.gov",
    "cdc.gov",
    "who.int",
    "un.org",
    "oecd.org",
    "europa.eu",
    "science.org",
    "pnas.org",
    "pubmed.ncbi.nlm.nih.gov",
}

# ---------------------------------------------------------------------------
# Explicit deny-list. Checked before the whitelist so a broad parent domain
# can never accidentally re-admit one of these hosts via a subdomain match.
# ---------------------------------------------------------------------------
BLOCKED_DOMAINS: set[str] = {
    "baidu.com",
    "qq.com",
    "sohu.com",
    "huxiu.com",
    "163.com",
    "sina.com.cn",
    "sina.com",
    "zhihu.com",
    "weibo.com",
    "toutiao.com",
    "ifeng.com",
    "thepaper.cn",
    "caixin.com",
    "csdn.net",
    "bilibili.com",
    "wikipedia.org",
    "wikiwand.com",
    "wikimedia.org",
    "britannica.com",
    "baike.com",
    "wenku.com",
}

_CATEGORY_LABELS = {
    "media": "Top30 公信力媒体",
    "fact_checker": "专业事实核查机构",
    "search_engine": "全球搜索引擎入口",
    "authority": "权威一手资料机构",
}


def _host(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return ""
    if "@" in host:
        host = host.rsplit("@", 1)[-1]
    if ":" in host:
        host = host.split(":", 1)[0]
    return host.rstrip(".")


def is_blocked(host: str) -> bool:
    """True when the host belongs to an explicitly rejected domain family."""
    return any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS)


def classify_source(url: str) -> Tuple[str | None, str]:
    """Return ``(category, host)``; ``category`` is ``None`` for untrusted URLs.

    Categories: media / fact_checker / search_engine / authority.
    A host is accepted only when it is a subdomain (or exact match) of a
    whitelisted domain, and is not covered by the deny-list.
    """
    host = _host(url)
    if not host or is_blocked(host):
        return None, host

    def matches(domains: set[str]) -> bool:
        return any(host == d or host.endswith("." + d) for d in domains)

    if matches(MEDIA_DOMAINS):
        return "media", host
    if matches(FACTCHECK_DOMAINS):
        return "fact_checker", host
    if matches(SEARCH_ENGINE_DOMAINS):
        return "search_engine", host
    if matches(AUTHORITY_DOMAINS):
        return "authority", host
    return None, host


def is_trusted_source(url: str) -> bool:
    category, _ = classify_source(url)
    return category is not None


def filter_trusted(hits: List[Dict]) -> List[Dict]:
    """Filter a list of search hits and tag each survivor with ``source_type``."""
    out: List[Dict] = []
    for hit in hits:
        if not isinstance(hit, dict):
            continue
        category, host = classify_source(str(hit.get("url", "")))
        if category is None:
            continue
        item = dict(hit)
        item["source_type"] = category
        item["source_type_label"] = _CATEGORY_LABELS[category]
        item["host"] = host
        out.append(item)
    return out


def source_policy_payload() -> Dict:
    """Structured description of the policy, exposed through the API/UI."""
    return {
        "policy": "strict_whitelist",
        "media_count": len(TOP_MEDIA),
        "media": [
            {"rank": m["rank"], "name": m["name"], "domain": m["domain"]}
            for m in TOP_MEDIA
        ],
        "fact_checkers": sorted(FACTCHECK_DOMAINS),
        "search_engines": sorted(SEARCH_ENGINE_DOMAINS),
        "authorities": sorted(AUTHORITY_DOMAINS),
        "blocked_examples": sorted(BLOCKED_DOMAINS),
        "note": (
            "仅收录全球公信力靠前的媒体、专业事实核查机构、国际搜索引擎入口与权威一手资料机构。"
            "百度/QQ/搜狐/虎嗅/维基百科等聚合站、百科站与内容农场不进入证据池。"
        ),
    }
