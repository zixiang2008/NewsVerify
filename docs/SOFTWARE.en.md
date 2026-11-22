# NewsVerify Software Specification

**Version:** 0.8.3 (Sieve) · **Release date:** 2026-11-23  
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

#### Trusted source whitelist (since v0.5.2)

The evidence pool uses a strict whitelist (`app/verification/source_policy.py`) with four allowed categories:

| Category | Scope | Reason |
| --- | --- | --- |
| Top 30 credible media | Reuters, AP, AFP, BBC and 26 others, plus authoritative domain variants | Cross-check baseline |
| Professional fact-checkers | Snopes, FactCheck.org, PolitiFact, Full Fact, AFP Fact Check, Lead Stories, etc. | Dedicated review of public claims |
| Global search engines | Google, Bing, DuckDuckGo, Yahoo, Brave, Startpage | Traceable retrieval entry points only, not editorial evidence |
| Authoritative primary sources | NASA, NOAA, WHO, UN, OECD, Science, PNAS, etc. | Directly verifiable original material |

Baidu Baike/Wenku, QQ, Sohu, Huxiu, Wikipedia and similar aggregators, encyclopedias and content farms are rejected during retrieval. They never enter the evidence pool or appear as openable source links in the console. The whitelist is published through `/api/source-policy` and a dashboard panel for auditability.

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
| Front-end JavaScript syntax | `node --check` passed; rendered script about 27.7k characters after v0.5.1 |
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

## 7.5 New in v0.6.0

- **Themes & music**: nine switchable themes (Aurora/Paper/Slate/Terminal/Ocean/Forest/Sunset/Violet/Mono) with local persistence; generative Web Audio ambient music (rain/waves/forest/night) with play/stop, track switching and volume, no external audio files.
- **Readable sources & visuals**: permanent scrollbar on the Top 30 panel; each evidence title shows a bracketed tag with outlet, global credibility rank, factual grade and report date.
- **Compliant collection** (`app/ingest/open_web.py`): public RSS / Google News RSS widen candidate discovery; robots.txt is respected, per-host rate limiting and bounded retries are used; no login/paywall/CAPTCHA bypass; every candidate still passes the trusted-source whitelist.
- **Multi-IM access** (`app/integrations/`): following the adapter + config-driven + unified-entry pattern of mature frameworks (NoneBot/OneBot, Kirara AI), adapters for Telegram, Discord, Slack, Feishu, DingTalk, WeCom, WeChat OA, QQ/OneBot, LINE, Matrix and generic webhooks; unified entry `POST /api/v1/im/{key}/webhook`.
- **Admin console** `/admin` (PIN `1314`): view masked API config, channel status and send test replies; `.env` changes require a container restart.
- **Theory page** `/theory`: public page with methodology, credibility-band origins, an SVG system diagram, itemised citations and academic/global assessment.

## 7.6 New in v0.6.1 — ambient sound library

- **20 generative soundscapes** (up from 4): white noise, singing bowl, Zen garden, outdoor birds, gentle rain, thunderstorm, mountain stream, wind chimes, summer crickets, campfire, temple bell, moonlight, bamboo grove, falling snow and more. Each track is composed of one or more `noise` / `pad` / `chirp` / `strike` layers synthesised in real time with Web Audio — no external audio files and no network requests.
- **Interaction**: clicking a sound starts it immediately; clicking the playing sound again stops it; clicking another sound switches to it. The list is scrollable so all 20 are reachable, and the play/stop button remains at the bottom of the panel.
- **Auto-hide**: the panel fades out after 5 seconds without interaction and can also be closed with the × button. Any click, mouse move, drag or wheel event restarts the timer. Fading out only collapses the panel — playback continues.
- **Volume**: the range input uses `oninput`, so changes apply while dragging, with a percentage readout. The selected track and volume persist in `localStorage` (`nv_music_track`, `nv_music_vol`).
- **Verification**: rendered-HTML JavaScript syntax validation (`ast` + `node --check`) and an interaction simulation test (play / stop / switch / volume) run before release.

## 7.7 New in v0.7.0 — interactive IM onboarding wizard

- **Design reference**: the adapter-driven, config-based WebUI wizards of AstrBot / NoneBot / Koishi — but **without adopting their runtime** (which would bloat NAS dependencies and rewrite the architecture). Only the interactive configuration experience is added on top of the existing `app/integrations/`.
- **Wizard** `/admin/im`: 11 mainstream platforms (Telegram, Discord, Slack, Feishu, DingTalk, WeCom, WeChat OA, QQ/OneBot, LINE, Matrix, generic webhook) shown as cards. Four steps: (1) official credential instructions with direct admin-console links, (2) a dynamic credential form, (3) QR scan / inbound URL copy, (4) a real test message.
- **No code, no restart**: credentials are written to `im_channel_configs` (`app/integrations/channel_store.py`) and hot-loaded by `ChannelRegistry.set_db_credentials()` on save. Values are masked on read (`1234••••mnop`) and a mask placeholder never overwrites the real secret. Legacy `NV_IM_*` env vars remain as a compatibility fallback.
- **QR binding**: `segno` renders a `t.me/<bot>?start` SVG QR for Telegram; scanning and sending `/start` makes the unified webhook record `bound_chat_id`, and the wizard polls `/bind-status`. Feishu / DingTalk / WeCom / LINE / QQ OneBot use their own official scan flows, so the wizard surfaces official scan guidance plus one-click copy of the inbound URL.
- **Real tests**: `app/integrations/__init__.py` builds platform-native message bodies (Feishu `msg_type:text` + timestamp signature, DingTalk `msgtype:text` + HMAC-SHA256 signing, WeCom, Discord `content`, Slack `text`, LINE `messages`, Matrix `m.text`, Telegram Bot API); results and errors are written back to the status panel.
- **Verification**: 15 onboarding-logic checks cover guide completeness, masking/merging, platform payloads and signing, safe failure when unconfigured, and QR generation; rendered JS is checked with `node --check`.

## 7.8 New in v0.7.1 — theory page citation system and source verification

- **Content**: `app/web/theory.py` was expanded into a full theory document with eight sections: why a framework is needed, an overview of news-authenticity theory, theory-to-implementation mapping, methodology, credibility-band origins, system diagram, academic assessment, and source notes.
- **Theory overview**: organises research on judging news authenticity into four layers — philosophical (correspondence / coherence / verificationist truth), cognitive (source credibility, confirmation bias), methodological (FEVER / AVeriTeC / Veracity / trafilatura) and institutional (MBFC / Ad Fontes / NewsGuard / AllSides / Reuters Institute).
- **Mapping table**: lists which part of the system each theory powers and how they combine into the chain "philosophy → output form, cognition → bias control, method → reproducible pipeline, institutions → source ranking".
- **Source notes**: in-text `[1]`–`[17]` citations link to the end section; each entry gives original URLs (arXiv / ACL Anthology / DOI / official pages, all sources where multiple exist), the earliest publishing institution, year, theoretical basis and system use. 27 distinct original URLs in total.
- **Source verification**: fixed wrong references in the old page — FEVER → arXiv:1803.05355 (NAACL 2018), AVeriTeC → arXiv:2305.13117 (NeurIPS 2023), trafilatura → ACL 2021.acl-demo.15; added foundational sources such as Hovland & Weiss 1951 (DOI 10.1086/266350, Yale), Nickerson 1998 (DOI 10.1037/1089-2680.2.2.175, Tufts), and the Stanford Encyclopedia of Philosophy "Truth" entry.
- **Verification**: `py_compile` passes; in-text citation numbers exactly match source-note numbers (1–17); HTML tag closure checks all pass; no leftover incorrect arXiv IDs.

### 7.9 New in v0.7.2 — Interactive Tracking Mind Map and bug-fix pass

- **Tracking Mind Map** (`showMindmap` / `showEventMindmap` in `app/web/app.py`), answering the need for a more intuitive presentation of each story's completeness, offers two views.
  - **Overview**: with no event ID, a card grid shows every task's status, verdict, claim count, media coverage and tracking flag; clicking a card opens that story's mind map.
  - **Per-story mind map**: the story is the root, expanding into six collapsible branches — ① claims & verdicts (each claim + label + confidence) ② evidence & provenance (deduplicated sources, clickable originals, media ranks) ③ media coverage (Top-30 lit count + outlet names) ④ continuous tracking (active state, next check, readable update log) ⑤ processing progress (timeline) ⑥ job history (attempts and timestamps).
  - **Interaction**: every node expands/collapses on click (`mmToggle`), with expand/collapse-all (`mmExpandAll`); the root node and toolbar jump to full detail; the `_modalView` marker prevents polling from overwriting a switched view.
  - **Styling**: pure CSS variables (dotted canvas, gradient root, state-coloured borders) that adapt to all 9 themes, with no external dependency.
- **Readable tracking updates**: `Notification.kind` now stores summaries such as "evidence change · N sources" / "tracking started · baseline", shown in the UI instead of a bare 64-character hash.
- **Bug fixes**: see CHANGELOG v0.7.2 — subscription creation from `freq`, progress preservation, list tracking-node state, polling cleanup, multi-channel tracking notifications, Top-30 emptiness check, recheck original text, v1 track de-duplication and modal escaping.

### 7.10 New in v0.7.3 — Connected mind maps, three layouts and sharing

- **Link engine**: `app/web/mindmap_asset.py` holds shared CSS/JS. A model built from `/api/events/{id}` data (root → six branches → leaves) is turned into absolutely positioned nodes plus SVG cubic bezier links, coloured per branch and tipped with arrowheads — fixing the v0.7.2 bug where the connector pseudo-element had zero height and nothing was visibly connected.
- **Three layouts**: tree (left→right, for reading claim by claim), waterfall (top→down, for pipeline and timelines) and radial (circular, for the whole relationship graph). The toolbar persists the choice in `localStorage`; overview, embedded detail map, standalone map and share page reuse one model and one renderer.
- **A map for every story**: `renderEvents()` calls `mmRenderMinis()` so each task card carries a four-branch mini map; clicking it opens the full six-branch map. The detail modal embeds an interactive map via `mmRenderInlineDetail()` while keeping polling view isolation.
- **Sharing**: `POST /api/mindmap/share` stores a snapshot in `mindmap_shares` and returns a random token URL. `GET /share/{token}` is a public read-only page (layout/theme switching, SVG/PNG export) with a segno QR code. Shared content is a static snapshot containing no admin credentials; the delete endpoint revokes a link. The middleware allows only the share page and snapshot GET through without PIN.
- **Readability**: six-colour legend, branch icons, short reading hints, expand/collapse and zoom. SVG and 2× PNG exports are generated locally with no external dependency.

---

## 7.9 New in v0.8.0 — design system, accounts and Agent API

- **NVDS** centralises themes and components in `app/web/design.py`; the console, login, registration, admin and API console all use the same tokens, surfaces and motion.
- **Accounts**: login is `username + 4-digit PIN`; `/register` needs a 6-digit invitation code; sessions are HMAC-signed cookies. Built-in super admins `caishen/1314` and `kayla/0720` are seeded on startup.
- **Invitation management** at `/admin/accounts`: batch generate codes (1–200), choose role, usage limit and expiry, copy per-code or batch instructions containing the registration URL, and revoke codes.
- **API keys** at `/admin/api`: create keys with `read`/`write`/`admin` scopes, enable/disable, revoke, counters and last-used timestamps. Runtime settings (master switch, write switch, result cap, public base URL, Agent note) persist in the database.
- **Agent-facing APIs**: `/api/v1/query/news`, `/api/v1/events/{id}/process`, `/api/v1/events/{id}/mindmap`, `/api/v1/jobs/{id}`, `/api/v1/keys/me`.
- **Debugging**: the API console renders request parameters, executes live calls, and generates cURL / Python / JavaScript samples plus a copyable Agent system prompt.

---

## 8. Limitations

- Ratings are references, not official licences; the media order is consultative.
- Search engines can be rate-limited; coverage may be incomplete for very new or non-indexed events.
- LLM judgement is probabilistic and must be read together with evidence and gaps.
- The PIN protects a personal console; for multi-user exposure, add HTTPS termination, per-user auth and rate limiting.
- Results are a snapshot in time. Continuous tracking exists precisely because facts change.
