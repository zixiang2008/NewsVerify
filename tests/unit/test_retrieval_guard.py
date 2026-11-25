"""Regression tests for the 2026-11-24 retrieval-layer incident."""

from app.ingest.open_web import (
    _google_news_rss_url,
    _is_public_feed,
    _extract_article_id,
)
from app.verification.evidence import is_block_page
from app.verification.judge import judge_claim
from app.verification.search import filter_relevant


def test_google_news_locale_uses_real_ceid():
    url = _google_news_rss_url("Pacific Ocean", "en-US")
    assert "ceid=US:en" in url
    cn = _google_news_rss_url("太平洋", "zh-CN")
    assert "ceid=CN:zh-Hans" in cn


def test_public_rss_feed_exempt_from_site_robots_but_not_html():
    assert _is_public_feed("https://news.google.com/rss/search?q=x")
    assert not _is_public_feed("https://news.google.com/articles/abc")
    assert not _is_public_feed("https://example.com/rss/search?q=x")


def test_extract_google_news_article_id():
    assert _extract_article_id(
        "https://news.google.com/rss/articles/CBMiabc?oc=5") == "CBMiabc"
    assert _extract_article_id("https://www.bbc.com/news") is None


def test_block_page_is_rejected():
    assert is_block_page("Just a moment...", "Just a moment... Enable JavaScript and cookies to continue")
    assert is_block_page("", "Forbidden / You don't have permission to access this resource")
    assert not is_block_page("Pacific Ocean", "The Pacific Ocean is the largest ocean on Earth. " * 20)


def test_relevance_gate_drops_zero_overlap():
    hits = [
        {"title": "Summer Place Apartment Homes", "url": "https://example.com", "snippet": "rentals"},
        {"title": "The Pacific Ocean", "url": "https://www.bbc.com/news", "snippet": "largest ocean on Earth"},
    ]
    kept = filter_relevant("Pacific Ocean largest ocean", hits)
    assert len(kept) == 1 and "Pacific" in kept[0]["title"]


async def test_supported_without_openable_url_is_downgraded(monkeypatch):
    async def _fake(self, system, user, model=None):
        return {
            "label": "supported", "confidence": 0.99, "rationale": "常识",
            "counter_argument": "", "evidence_gaps": [],
            "cited_urls": ["https://not-in-evidence.example"],
        }

    monkeypatch.setattr("app.verification.judge.LLMClient.chat_json", _fake)
    result = await judge_claim("太平洋是地球上最大的海洋。", [])
    assert result["label"] == "insufficient_evidence"
    assert result["confidence"] <= 0.35
    assert result["cited_urls"] == []
    assert any("判定守卫" in gap for gap in result["evidence_gaps"])


async def test_cited_urls_must_come_from_evidence(monkeypatch):
    async def _fake(self, system, user, model=None):
        return {
            "label": "supported", "confidence": 0.9, "rationale": "有证据",
            "counter_argument": "", "evidence_gaps": [],
            "cited_urls": ["https://www.bbc.com/real", "https://hallucinated.example"],
        }

    monkeypatch.setattr("app.verification.judge.LLMClient.chat_json", _fake)
    result = await judge_claim("x", [{"url": "https://www.bbc.com/real", "fetch_error": None}])
    assert result["label"] == "supported"
    assert result["cited_urls"] == ["https://www.bbc.com/real"]
