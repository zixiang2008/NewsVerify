# NewsVerify

**Self-hosted, auditable fact-checking workspace.** Version **0.5.0 (Atlas)** · 2026-11-17.

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

## What is new in 0.5.0

- Four switchable UI templates: **Aurora**, **Paper**, **Slate**, **Terminal**.
- Top navigation, version chip and a **Version & Updates** dialog.
- Single source of truth for versioning in `app/version.py`.
- Complete English / Chinese / Japanese documentation and a one-command GitHub sync script.
- NAS runtime rebuilt and verified against the latest source.

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
