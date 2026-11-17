# NewsVerify Software Specification

**Version:** 0.5.0 (Atlas) · **Release date:** 2026-11-17  
**Repository:** https://github.com/zixiang2008/NewsVerify  
**Live console:** https://new.caishen.today (LAN: `http://192.168.8.253:8095`)

This document explains why NewsVerify exists, what research it draws on, how it reasons from evidence to a verdict, how every data source is combined, and what the latest local experiment produced. It is written for operators, reviewers and agents that need to understand or maintain the system.

---

## 1. Why this software exists

News feeds, social platforms and generative models produce claims faster than any person can check them. A screenshot, a repost and an AI summary can all look equally confident while having very different evidentiary support. Manual fact-checking is slow; simple keyword matching is unreliable; and closed commercial checkers cannot be inspected or deployed on private infrastructure.

NewsVerify is a **self-hosted, auditable claim-verification workspace**. It does not ask the reader to trust a single model output. Instead it:

1. splits a news item into independently checkable claims;
2. retrieves open-web evidence for each claim, including refutation-oriented queries;
3. collapses syndicated copies so that "many outlets saying the same thing" is not mistaken for independent confirmation;
4. asks an LLM to choose one of six constrained verdict labels, always with rationale, counter-evidence and gaps;
5. cross-checks the claim against a 30-outlet media panel and records openable source links;
6. keeps watching the event and notifies only when the evidence fingerprint actually changes.

The design motto is: **when evidence is absent, say "insufficient evidence" — never invent support.**

---

## 2. Research materials and prior work

NewsVerify is an engineering synthesis of several public research and ratings traditions. It does **not** purchase or redistribute licensed rating databases, and it does not fabricate official scores.

| Material | What it contributes | How NewsVerify uses it |
| --- | --- | --- |
| FEVER-style claim verification | Decompose a document into atomic, verifiable claims; retrieve supporting and refuting evidence separately | `app/verification/claims.py`, `evidence.py` |
| AVeriTeC (real-world claim verification) | Evidence-first verification and explicit evidence gaps; uncertainty must be preserved | Verdict schema includes `evidence_gaps`, `counter_argument` and six labels |
| Google Fact Check Tools API | Professional fact-check reviews with `textualRating` and review date | Optional augmentation through `search_google_factcheck()` when an API key is configured |
| Media Bias/Fact Check (MBFC) | Public "Factual Reporting" tiers (Very High / High / Mostly Factual) | Reference scale for the `factual` field of the Top 30 panel; no paid API is called |
| Reuters Institute *Digital News Report* | Cross-country public trust in news brands | Background input for ordering the panel; not an article-level score |
| NewsGuard, Ad Fontes Media, AllSides | Credibility / bias taxonomies | Recorded as `not_connected` metadata; no official score is displayed unless licensed data is supplied |
| Pew Research Center, Reporters Without Borders | Audience behaviour and press-freedom environment | Recorded as `context_only`; used to remind reviewers that country context is not truth value |
| Veracity (arXiv:2506.15794) and similar open systems | Source transparency: reliability + explanation + traceable URL; source independence/diversity | Inspired `independence_chain_id`, clickable source lists and report counts |
| OpenAI-compatible LLM APIs | Structured reasoning over retrieved evidence only | Primary/backup endpoints with failover; constrained JSON verdict output |

The six-rating-system metadata lives in `app/ratings/systems.py`. Every entry states its licence status. This is deliberately conservative: a missing rating is shown as missing, not guessed.

---

## 3. Argumentation method and the conclusion it produces

### 3.1 The six-stage pipeline

| Stage | Operation | Output |
| --- | --- | --- |
| 1. Claim decomposition | LLM splits input text into atomic claims, bounded by configuration | `claims` rows |
| 2. Evidence retrieval | Two query families per claim: original wording and refutation-oriented wording | `sources` + `evidence` candidates |
| 3. Independence judgement | URL deduplication plus a body-fingerprint-based `independence_chain_id`; syndicated copies collapse | Independent evidence set |
| 4. LLM judgement | Structured prompt over evidence snippets only | `verdicts` with label, confidence, rationale, counter-argument, gaps |
| 5. Media cross-check | Broad search results are domain-matched to the Top 30 panel; a few key outlets get supplemental `site:` queries | 30 cells with hit counts and openable URLs |
| 6. Continuous tracking | Evidence and verdict fingerprints are compared at 6h / 24h / weekly intervals | Notifications only on substantive change |

Each step writes a progress entry into `jobs.result.progress`, which the web console renders as a live timeline.

### 3.2 Allowed conclusions

The judge must choose exactly one label:

- `supported` — sufficient supporting evidence;
- `refuted` — sufficient counter-evidence;
- `mixed` — both sides present;
- `insufficient_evidence` — no reliable evidence found (default fallback);
- `outdated` — once true, now changed;
- `not_checkable` — subjective, future-tense or otherwise untestable.

### 3.3 Rules that prevent over-claiming

- An allegation is not a fact; an investigation is not a conviction.
- No evidence is not proof of falsehood.
- An unreadable page is marked as a fetch failure, not counted as absence of evidence.
- A verdict without an openable source URL is rejected or downgraded to `insufficient_evidence`.
- Reposts of the same wire story count as one independence chain.
- Political or fast-moving topics keep their time bounds and uncertainty.
- All externally fetched URLs pass an SSRF check before access.

**Resulting conclusion format:** per claim, a constrained label + confidence + rationale + counter-argument + evidence gaps + cited URLs; per event, a summary plus a 30-outlet coverage map and a tracking state. The system reports what the evidence supports *at retrieval time*; it does not claim permanent truth.

---

## 4. Data sources, provenance and combination

### 4.1 Input channels

| Channel | Entry point | Notes |
| --- | --- | --- |
| Web console | `POST /submit` or `POST /api/v1/check` | Textarea plus mode (`full` / `top30` / `method`) and frequency |
| Telegram Bot | `/check`, `/deep`, `/track`, `/status`, `/history` | aiogram long polling; graceful degradation if token is invalid |
| Public API v1 | API-Key header | Machine integration for agents |

### 4.2 Retrieval and extraction

- `unified_search()` selects a provider from configuration: `ddgs` (function name retained for compatibility), Brave Search or SearXNG.
- In the NAS network, `search_duckduckgo()` explicitly locks the `yahoo` backend first and falls back to `duckduckgo`; this avoids ddgs polling seven backends and reduced Top 30 checking from about 146 s to about 44 s.
- Google Fact Check results, when configured, are prepended as official review material and then URL-deduplicated.
- `fetch_url()` validates the URL, blocks private network targets and computes a content hash.
- `extract_text()` uses trafilatura-style extraction to obtain readable body text; snippets are capped before being sent to the judge.

### 4.3 Source model and independence

Each evidence item stores `url`, `domain`, `content_hash`, `independence_chain_id`, `snippet_hash`, fetch status and optional publication time. The chain ID combines the domain with a SHA-256 prefix of the first 80 normalised body characters. Identical chains are collapsed, so a press-release cascade is not mistaken for many witnesses.

### 4.4 Top 30 media panel

`app/verification/top_media.py` defines 30 outlets ordered by "factual accuracy + editorial independence":

1. Global wires and public broadcasters — Reuters, AP, AFP, BBC, NPR, PBS, DW, France 24, NHK World, ABC AU.
2. National / international newspapers and business media — NYT, Washington Post, Guardian, FT, WSJ, Economist, Time, Newsweek, CNN, Al Jazeera.
3. Professional fact-checkers, academic and regional authorities — Snopes, FactCheck.org, Politifact, Full Fact, The Conversation, Scientific American, Nature News, The Canadian Press, The Hindu, Sydney Morning Herald.

For each claim, `check_top_media()` first runs a small number of broad searches and maps results to the panel by domain (handling `www.` and common aliases such as `bbc.co.uk`); then it runs a limited number of supplemental `site:` queries for important unmatched outlets. The UI lights a media dot green when `hit_count > 0`, otherwise gray, and exposes every source URL.

### 4.5 Combination order

```
User input
  -> Event + queued Job
  -> claims[]
  -> (search original + search refutation) -> sources[] -> independence dedup
  -> verdicts[] (six-label constrained LLM output)
  -> Top30 coverage map (domain matching + site: supplement)
  -> job.result { summary, progress, top_media, media_hits, total_reports }
  -> Telegram push + web rendering
  -> Subscription polling -> fingerprint diff -> Notification
```

The LLM is called through an OpenAI-compatible client with primary/backup endpoints (`LLM_BASE_URL`, `LLM_BASE_URL_FALLBACK`). Internal retries are disabled; endpoint switching is handled by `app/verification/llm.py` with a small circuit breaker, preventing long retry storms.

### 4.6 Persistence

PostgreSQL tables: `events`, `claims`, `sources`, `evidence`, `verdicts`, `jobs`, `subscriptions`, `notifications`. Child tables use `ON DELETE CASCADE`. Job results are JSON, which keeps the evolving pipeline schema flexible while the core relational tables remain auditable.

---

## 5. Final experimental results

The following results come from the local deployment on a Synology N150-P NAS, not from a synthetic benchmark.

| Check | Result |
| --- | --- |
| `/health` | HTTP 200 |
| Front-end JavaScript syntax | `node --check` passed; rendered script about 27.7k characters after v0.5.0 |
| `/api/top-media` | 30 outlets returned with rank, factual tier, independence, type and URL |
| End-to-end full check | `done` in about 101 s for the verified sample |
| Media cross-check | 10 of 30 outlets lit; 20 openable related sources |
| LAN and public access | Both `http://192.168.8.253:8095` and `https://new.caishen.today` served the updated build |
| API failover | Primary and backup LLM endpoints both returned HTTP 200; forced primary failure switched to backup successfully |
| Search optimisation | Locks `yahoo` first; Top 30 stage approximately 146 s -> 44 s in local tests |
| Historical cleanup | 15 failed jobs and 1 orphaned test event removed after backup; remaining 8 events all succeeded |
| Multi-theme UI | Four templates switch live; choice persisted locally; version modal shows release history |

Interpretation: the pipeline produces a stable, inspectable result within roughly two minutes on the local NAS. The dominant cost is media cross-checking, which is why broad-search domain matching is used before targeted `site:` queries. The system is designed for personal and small-team use; it is not a legal or professional adjudication authority.

---

## 6. How to operate it

### 6.1 Web console

1. Open the LAN or public URL and enter the PIN.
2. Choose a theme template in the header if desired.
3. Paste text or a URL, select mode and tracking frequency, then submit.
4. The task appears immediately at the top of the history; its detail dialog refreshes every three seconds while running.
5. Click a task for verdicts, evidence, progress timeline and the 30-outlet media map.
6. Use **追踪状态** for all updates, or **设置** to change frequency, next run time and pause state.
7. Watch the system panel at the bottom for CPU, memory, disk and live API status.

### 6.2 Telegram

`/help`, `/check <text>`, `/deep <text>`, `/track <event_id> [6h|24h|week]`, `/untrack`, `/status`, `/history`, `/privacy`.

### 6.3 Public API v1

```bash
curl -H "X-API-Key: $API_KEY" https://new.caishen.today/api/v1/version
curl -H "X-API-Key: $API_KEY" -H 'Content-Type: application/json' \
  -d '{"text":"...","mode":"full","freq":"none"}' \
  https://new.caishen.today/api/v1/check
```

---

## 7. Versioning and release workflow

`app/version.py` is the only place where the version number and release notes are authored. The web badge, login page, `/api/version`, `/api/v1/status`, `pyproject.toml`, `compose.yaml`, README files and changelog all derive from or mirror it.

For every release:

1. Update `VERSION`, `RELEASE_DATE`, `CODENAME` and `RELEASES` in `app/version.py`.
2. Mirror the version in `pyproject.toml`, `compose.yaml` and `CHANGELOG.md`.
3. Update the English, Chinese and Japanese README/software documents.
4. Run `./scripts/sync_github.sh` to commit and push the sanitised source.
5. Deploy to the NAS and verify `/health`, `/api/version` and the UI version badge.

---

## 8. Limitations

- Ratings are references, not official licences; the media order is consultative.
- Search engines can be rate-limited; coverage may be incomplete for very new or non-indexed events.
- LLM judgement is probabilistic and must be read together with evidence and gaps.
- The PIN protects a personal console; for multi-user exposure, add HTTPS termination, per-user auth and rate limiting.
- Results are a snapshot in time. Continuous tracking exists precisely because facts change.
