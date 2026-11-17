from __future__ import annotations

from typing import List, Dict

# ---------------------------------------------------------------------------
# Top 30 全球主要媒体（按“事实准确性 + 编辑独立性”综合排序）
#
# 排序依据（借鉴 Media Bias/Fact Check 的 Factual Reporting 分级、Reuters
# Institute《Digital News Report》的公众信任度研究，以及 Veracity 等开源核查
# 项目的来源透明度实践）：
#   - factual: MBFC 事实报道等级（Very High / High / Mostly Factual）
#   - independence: 编辑独立性/公共属性（通讯社、公共广播、非营利 > 商业媒体）
#   - 综合序 = 通讯社/公共广播优先，再按事实准确性与全球影响力排列。
#
# 说明：这是"参考性榜单"，综合公开研究整理，非任何机构官方认证的精确名次；
# 不同机构口径不同。仅作核查时优先交叉验证的来源，不编造官方评级分数。
# ---------------------------------------------------------------------------
TOP_MEDIA = [
    # 全球通讯社 / 公共广播（高事实性 + 高独立性）
    {"rank": 1,  "name": "Reuters", "domain": "reuters.com", "factual": "Very High", "independence": "high", "type": "通讯社", "why": "全球性通讯社，严格事实核查与多源验证，被大量媒体二次引用。"},
    {"rank": 2,  "name": "Associated Press (AP)", "domain": "apnews.com", "factual": "Very High", "independence": "high", "type": "通讯社", "why": "美国非营利新闻合作社，全球网络，事实准确性高。"},
    {"rank": 3,  "name": "Agence France-Presse (AFP)", "domain": "afp.com", "factual": "Very High", "independence": "high", "type": "通讯社", "why": "法国全球通讯社，多语言多国驻站，事实核查传统强。"},
    {"rank": 4,  "name": "BBC News", "domain": "bbc.com", "factual": "Very High", "independence": "high", "type": "公共广播", "why": "英国公共广播，编辑独立，BBC Verify 事实核查团队活跃。"},
    {"rank": 5,  "name": "NPR", "domain": "npr.org", "factual": "Very High", "independence": "high", "type": "公共广播", "why": "美国非营利公共广播，深度报道与事实核查声誉高。"},
    {"rank": 6,  "name": "PBS NewsHour", "domain": "pbs.org", "factual": "Very High", "independence": "high", "type": "公共广播", "why": "美国公共电视，长篇事实性报道，政治中立性较好。"},
    {"rank": 7,  "name": "Deutsche Welle (DW)", "domain": "dw.com", "factual": "Very High", "independence": "high", "type": "公共广播", "why": "德国国际公共广播，多维国际报道，事实核查严格。"},
    {"rank": 8,  "name": "France 24", "domain": "france24.com", "factual": "Very High", "independence": "high", "type": "公共广播", "why": "法国国际新闻频道，多语言，国际事实报道。"},
    {"rank": 9,  "name": "NHK World", "domain": "nhk.or.jp", "factual": "Very High", "independence": "high", "type": "公共广播", "why": "日本公共广播 NHK 国际频道，事实准确性高。"},
    {"rank": 10, "name": "ABC News (AU)", "domain": "abc.net.au", "factual": "Very High", "independence": "high", "type": "公共广播", "why": "澳大利亚公共广播，编辑独立，事实核查严格。"},
    # 国际/全国性权威报纸
    {"rank": 11, "name": "The New York Times", "domain": "nytimes.com", "factual": "High", "independence": "medium", "type": "全国性报纸", "why": "美国全国性报纸，独立事实核查与调查报道团队。"},
    {"rank": 12, "name": "The Washington Post", "domain": "washingtonpost.com", "factual": "High", "independence": "medium", "type": "全国性报纸", "why": "美国全国性报纸，调查报道与事实核查（Fact Checker）知名。"},
    {"rank": 13, "name": "The Guardian", "domain": "theguardian.com", "factual": "High", "independence": "medium", "type": "全国性报纸", "why": "英国全国性报纸，调查报道与事实核查团队活跃。"},
    {"rank": 14, "name": "Financial Times", "domain": "ft.com", "factual": "Very High", "independence": "medium", "type": "财经媒体", "why": "国际财经媒体，数据驱动，事实准确性高。"},
    {"rank": 15, "name": "Wall Street Journal", "domain": "wsj.com", "factual": "High", "independence": "medium", "type": "财经媒体", "why": "美国财经大报，事实准确性与数据新闻声誉高。"},
    {"rank": 16, "name": "The Economist", "domain": "economist.com", "factual": "High", "independence": "medium", "type": "周刊", "why": "英国周刊，研究型报道，数据与分析严谨。"},
    {"rank": 17, "name": "Time", "domain": "time.com", "factual": "High", "independence": "medium", "type": "新闻周刊", "why": "美国新闻周刊，全球报道与事实核查。"},
    {"rank": 18, "name": "Newsweek", "domain": "newsweek.com", "factual": "High", "independence": "medium", "type": "新闻周刊", "why": "美国新闻周刊，国际与国内事实报道。"},
    {"rank": 19, "name": "CNN", "domain": "cnn.com", "factual": "High", "independence": "medium", "type": "电视新闻", "why": "美国有线新闻网，全球报道，设有事实核查栏目。"},
    {"rank": 20, "name": "Al Jazeera", "domain": "aljazeera.com", "factual": "High", "independence": "medium", "type": "国际新闻", "why": "卡塔尔国际新闻网，覆盖全球南方视角，事实核查团队活跃。"},
    # 专业事实核查 / 非营利 / 区域权威
    {"rank": 21, "name": "Snopes", "domain": "snopes.com", "factual": "Very High", "independence": "high", "type": "事实核查", "why": "老牌事实核查网站，专攻谣言与网络传闻。"},
    {"rank": 22, "name": "FactCheck.org", "domain": "factcheck.org", "factual": "Very High", "independence": "high", "type": "事实核查", "why": "Annenberg 公共政策中心下属，非营利事实核查。"},
    {"rank": 23, "name": "Politifact", "domain": "politifact.com", "factual": "Very High", "independence": "high", "type": "事实核查", "why": "Poynter 下属事实核查项目，评级体系透明。"},
    {"rank": 24, "name": "Full Fact", "domain": "fullfact.org", "factual": "Very High", "independence": "high", "type": "事实核查", "why": "英国独立事实核查慈善机构。"},
    {"rank": 25, "name": "The Conversation", "domain": "theconversation.com", "factual": "Very High", "independence": "high", "type": "学术媒体", "why": "学者撰写的analyzed新闻，学术来源可追溯。"},
    {"rank": 26, "name": "Scientific American", "domain": "scientificamerican.com", "factual": "Very High", "independence": "high", "type": "科学媒体", "why": "科学报道权威，同行评议来源。"},
    {"rank": 27, "name": "Nature News", "domain": "nature.com", "factual": "Very High", "independence": "high", "type": "科学媒体", "why": "顶级学术期刊新闻板块，科学事实严谨。"},
    {"rank": 28, "name": "The Canadian Press", "domain": "thecanadianpressnews.ca", "factual": "Very High", "independence": "high", "type": "通讯社", "why": "加拿大国家通讯社，事实准确性高。"},
    {"rank": 29, "name": "The Hindu", "domain": "thehindu.com", "factual": "High", "independence": "medium", "type": "全国性报纸", "why": "印度权威英文报纸，国际认可度高。"},
    {"rank": 30, "name": "Sydney Morning Herald", "domain": "smh.com.au", "factual": "High", "independence": "medium", "type": "全国性报纸", "why": "澳大利亚权威报纸，调查报道声誉高。"},
]

# 为兼容旧代码/前端，补回 url 字段（由 domain 推导）
for _m in TOP_MEDIA:
    _m["url"] = "https://www." + _m["domain"]

NOTE = (
    "参考性榜单，综合 Media Bias/Fact Check（MBFC）的事实报道分级、Reuters Institute"
    "《Digital News Report》的公众信任度研究，以及开源事实核查项目（如 Veracity）的来源透明度实践整理，"
    "按“事实准确性 + 编辑独立性”排序。非任何机构官方认证的精确名次；仅作核查交叉验证的优先来源。"
)


def _match_media(url: str) -> str | None:
    """把结果 URL 匹配到 Top30 榜单中的媒体域名。返回 domain 或 None。

    处理 www./子域名；对 bbc.com 同时接受 bbc.co.uk 等常见变体。
    """
    from urllib.parse import urlparse
    try:
        host = urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return None
    aliases = {
        "bbc.com": ["bbc.com", "bbc.co.uk"],
        "cnn.com": ["cnn.com"],
        "apnews.com": ["apnews.com"],
        "thehindu.com": ["thehindu.com", "hindustantimes.com"],
    }
    for m in TOP_MEDIA:
        d = m["domain"]
        cand = aliases.get(d, [d])
        if any(host == a or host.endswith("." + a) for a in cand):
            return d
    return None


async def check_top_media(claim_text: str, max_per: int = 2) -> List[Dict]:
    """对一条主张，检查 Top30 媒体中哪些报道了该信息。

    快速策略：先做少量通用搜索（避免 30 次 site: 请求被限流），把结果按域名
    归类到榜单；再对未命中的少数重点媒体做补充 site: 查询。返回全部 30 家，
    每家含 hit_count 与 hits，前端据此点亮/置灰。
    """
    from app.verification.search import search_duckduckgo
    from app.verification.source_policy import classify_source
    import asyncio
    from urllib.parse import urlparse

    def _hit(h):
        return {
            "title": h.get("title", ""), "url": h.get("url", ""), "snippet": h.get("snippet", ""),
            "source_type": h.get("source_type", ""),
        }

    def _clean(hits):
        """Drop Baidu/QQ/aggregator results before they reach the UI."""
        out = []
        for h in hits:
            if not isinstance(h, dict) or not h.get("url") or h.get("title") == "search error":
                continue
            category, host = classify_source(h["url"])
            if category is None:
                continue
            item = _hit(h)
            item["source_type"] = category
            item["host"] = host
            out.append(item)
        return out

    # 初始化每家媒体的结果骨架
    result = {m["rank"]: {
        "rank": m["rank"], "name": m["name"], "url": m["url"], "domain": m["domain"],
        "factual": m.get("factual", ""), "independence": m.get("independence", ""),
        "type": m.get("type", ""), "hits": [], "hit_count": 0,
    } for m in TOP_MEDIA}
    domain_to_rank = {m["domain"]: m["rank"] for m in TOP_MEDIA}

    # 1) 通用搜索：2 个查询并行，收集广泛结果并按域名归类（一次请求覆盖多家）
    queries = [claim_text[:160], f"{claim_text[:100]} news report"]
    searches = await asyncio.gather(
        *[asyncio.wait_for(search_duckduckgo(q, max_results=30), timeout=20) for q in queries],
        return_exceptions=True,
    )
    for res in searches:
        if not isinstance(res, list):
            continue
        for h in _clean(res):
            dom = _match_media(h["url"])
            if dom:
                r = domain_to_rank[dom]
                if len(result[r]["hits"]) < max_per:
                    result[r]["hits"].append(_hit(h))

    # 2) 对尚未命中、且是重点媒体（前 6 家）做补充 site: 查询（低并发）
    missing_top = [m for m in TOP_MEDIA[:6] if result[m["rank"]]["hit_count"] == 0]

    async def _site(m):
        q = f"site:{m['domain']} {claim_text[:120]}"
        try:
            hits = await asyncio.wait_for(search_duckduckgo(q, max_results=max_per), timeout=10)
        except Exception:
            hits = []
        return m["rank"], _clean(hits)

    if missing_top:
        # 每批 4 家，避免并发过高被重置
        for i in range(0, len(missing_top), 4):
            batch = missing_top[i:i + 4]
            for rank, hits in await asyncio.gather(*[_site(m) for m in batch], return_exceptions=True):
                if isinstance(hits, list):
                    result[rank]["hits"] = hits[:max_per]

    # 计算命中数
    for m in TOP_MEDIA:
        result[m["rank"]]["hit_count"] = len(result[m["rank"]]["hits"])
    return [result[m["rank"]] for m in TOP_MEDIA]
