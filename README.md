# NewsVerify

**Self-hosted, auditable fact-checking workspace.** Version **0.7.2 (Lens)** · 2026-11-18.

NewsVerify turns a news item into verifiable claims, searches open-web evidence, checks source independence, produces a constrained six-label verdict, cross-checks against 30 high-credibility media outlets, and keeps tracking the event for substantive changes.

- Public console: https://new.caishen.today
- LAN console: `http://192.168.8.253:8095`
- Source: https://github.com/zixiang2008/NewsVerify

## Start here

| Document | Language | Purpose |
| --- | --- | --- |
| [README.md](README.md) | English (default) | Quick start and documentation map |
| [README.zh-CN.md](README.zh-CN.md) | 简体中文 | 快速开始与文档导航 |
| [README.ja.md](README.ja.md) | 日本語 | クイックスタートと文書案内 |
| [docs/SOFTWARE.en.md](docs/SOFTWARE.en.md) | English | Full software specification |
| [docs/SOFTWARE.zh-CN.md](docs/SOFTWARE.zh-CN.md) | 中文 | 完整软件说明书 |
| [docs/SOFTWARE.ja.md](docs/SOFTWARE.ja.md) | 日本語 | ソフトウェア仕様書 |
| [docs/PROJECT.md](docs/PROJECT.md) | 中文 | Architecture, data model, deployment details |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | English | Six systems and verdict rules |
| [docs/API.md](docs/API.md) | English | Public API v1 reference |
| [CHANGELOG.md](CHANGELOG.md) | English | Version history |

## What is new in 0.7.2

- **Interactive Tracking Mind Map** (`🧠`): an overview of all news items, and a per-story expandable mind map (claims & verdicts, evidence, media coverage, tracking, progress, history). Readable tracking-update summaries replace bare hashes.
- **Bug-fix pass**: the submission frequency now actually creates a subscription; the progress timeline survives completion; the "tracking" node lights up correctly; view switching no longer gets overwritten by polling; tracking alerts broadcast to all configured IM channels; fixes to Top-30 queries, recheck, v1 track de-duplication and modal escaping.

## What is new in 0.7.1

- **Rebuilt `/theory` page**: a four-layer overview of how to judge news authenticity (philosophy / cognition / method / institutions), plus a mapping table showing which theory powers which part of the system.
- **Every citation verified and linked**: numbered `[1]`–`[17]` references with original URLs (arXiv / ACL Anthology / DOI / official pages), earliest publishing institution, year and theoretical basis — including foundational work such as Hovland & Weiss 1951 (source credibility) and Nickerson 1998 (confirmation bias).
- **Corrected wrong paper IDs** from the previous page (FEVER, AVeriTeC, trafilatura) and redrew the system diagram into five layers.

## What is new in 0.7.0

- **Interactive IM onboarding wizard** at `/admin/im`: connect 11 mainstream platforms in four guided steps — official credentials, fill a form, scan/copy the callback URL, run a real test. Modelled on the WebUI wizards of AstrBot / NoneBot / Koishi.
- **No more code or restarts**: credentials are saved to the database, masked on display, and take effect immediately. Telegram supports a scan-to-bind QR; Feishu / DingTalk / WeCom / LINE / QQ OneBot provide official scan entries and a one-click copy of the inbound URL.
- Ambient sound library expanded to **20 generative scenes** with click-to-play, click-again-to-stop and a 5-second auto-fade panel.

## What is new in 0.6.1

- **20-scene ambient sound library** (up from 4): white noise, singing bowl, Zen garden, outdoor birds, rain, thunderstorms, streams, wind chimes, crickets, campfire, temple bell, bamboo grove, falling snow and more — all synthesised locally with Web Audio, no external audio files.
- **Click to play**: click a sound to start it, click it again to stop, or click another one to switch. Volume adjusts live while dragging, with a percentage readout.
- The player panel **fades out after 5 seconds of inactivity**, can be closed manually, and fading out never interrupts playback. All 20 sounds are reachable via a scrollable list.

## What is new in 0.6.0

- **9 UI themes** (adds Ocean / Forest / Sunset / Violet / Mono) and an optional **ambient background music** player with 4 generative tracks and volume control.
- **30-media panel** now has a permanent scrollbar; each evidence item shows a bracketed tag with the outlet, its global credibility rank, factual grade and report date.
- **Compliant open-web collection**: public RSS / Google News RSS discovery, robots.txt respect, rate limiting and retries — still gated by the trusted-source whitelist.
- **Admin console** at `/admin` (PIN `1314`): inspect API configuration and manage/test mainstream instant-messaging webhook connectors (Telegram, Discord, Slack, Feishu, DingTalk, WeCom, WeChat OA, QQ/OneBot, LINE, Matrix, generic).
- Simplified topology diagram showing a single "all instant messengers" entry point.
- New public page **[/theory](app/web/theory.py)** "Rational News-Reading Theoretical Sources": methodology, the credibility-band system and its origins, a full diagram, itemised citations and academic/global assessment.

Previous release 0.5.2 added the strict trusted-source whitelist, `/api/source-policy` and historical cleanup tooling.

See [CHANGELOG.md](CHANGELOG.md) for the full history.

## Quick start on Synology NAS

```bash
cd /volume2/docker/newsverify
cp .env.example .env && chmod 600 .env
DOCKER=/volume2/@appstore/ContainerManager/usr/bin/docker
$DOCKER compose up -d --build
curl http://127.0.0.1:8095/health
curl http://127.0.0.1:8095/api/version
```

Inside Docker, a NAS-local LLM service must be addressed through the Docker gateway, for example `http://172.17.0.1:3065/v1`. Use `.env.example` as the configuration reference. Never commit `.env`.

## Interfaces

- **Web:** enter the PIN, paste a claim, choose mode and tracking frequency, then watch the live node timeline and 30-media coverage map.
- **Telegram:** `/check`, `/deep`, `/track`, `/untrack`, `/status`, `/history`, `/privacy`.
- **API v1:** `X-API-Key` authenticated endpoints under `/api/v1/`.

## Tech stack

Python 3.12 · FastAPI · aiogram · SQLAlchemy asyncpg · PostgreSQL 16 · OpenAI-compatible LLM with primary/backup failover · ddgs/Brave/SearXNG search · trafilatura extraction · Docker Compose.

## Safety and scope

PIN plus optional API-key authentication, SSRF checks on external URLs, independent-source deduplication and constrained verdict labels reduce false confidence. NewsVerify is a decision-support workspace, not a legal or professional adjudication authority. Results are snapshots; continuous tracking exists because facts change.

## Release workflow

1. Update `app/version.py`, `pyproject.toml`, `compose.yaml` and `CHANGELOG.md`.
2. Update all three language documents.
3. Run `./scripts/sync_github.sh` to publish sanitised source to GitHub.
4. Deploy to NAS and verify `/health`, `/api/version` and the UI version badge.
