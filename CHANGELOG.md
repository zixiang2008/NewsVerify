# Changelog

All notable changes to NewsVerify are documented here. The current version is **0.6.1 (Echo, 2026-11-17)**.

The single source of truth for the version is [`app/version.py`](app/version.py). Web UI, API, `pyproject.toml`, `compose.yaml` and documentation all follow it.

## 0.6.1 — Echo (2026-11-17)

### Added
- Ambient sound library expanded from 4 to **20 generative scenes**: white noise, singing bowl, Zen garden, morning birds, thunderstorm, mountain stream, wind chimes, summer crickets, campfire, temple bell, bamboo grove, falling snow and more.
- A layered Web Audio engine (`noise` / `pad` / `chirp` / `strike`) synthesises every scene locally — no external audio files or network requests.

### Changed
- Clicking a sound starts it immediately; clicking the playing sound again stops it; clicking another sound switches tracks. The separate play/stop button is still available.
- The music panel fades out after 5 seconds of inactivity and can also be closed manually; any interaction resets the timer, and fading out never stops playback. Sounds are listed in a scrollable area so all 20 are reachable.
- Volume now updates live while dragging, with a percentage readout; track and volume preferences remain in `localStorage`.
- Added rendered-HTML JavaScript syntax validation plus an interaction simulation test covering play / stop / switch / volume.

## 0.6.0 — Prism (2026-11-17)

### Added
- Nine switchable UI themes (adds Ocean / Forest / Sunset / Violet / Mono alongside Aurora / Paper / Slate / Terminal).
- Ambient background music player with four generative Web Audio tracks, play/stop, track switching and volume control (no external audio files).
- Unified instant-messaging adapter layer (`app/integrations/`) with a config-driven channel catalogue for Telegram, Discord, Slack, Feishu, DingTalk, WeCom, WeChat OA, QQ/OneBot, LINE, Matrix and generic webhooks.
- Admin console at `/admin` behind PIN `1314`: view (masked) API configuration and test/maintain IM webhook connectors; new endpoints `/api/admin/*`.
- Compliant open-web collector (`app/ingest/open_web.py`): public Google News RSS + custom feeds, robots.txt checks, polite rate limiting, bounded retries — all results still pass the trusted-source whitelist.
- Public theory page `/theory` (`app/web/theory.py`) covering methodology, credibility-band origins, a full SVG system diagram, itemised citations and academic/global assessment.
- Permanent scrollbar on the Top 30 media panel; each evidence item now shows a bracketed tag with outlet, global credibility rank, factual grade and report date.
- Evidence collection now skips search-engine domains as evidence (they are discovery entry points only) and adds `site:` queries against leading credible media to keep the evidence pool populated with real outlet articles.

### Changed
- System topology diagram now depicts one generic "instant messengers (incl. Telegram)" entry point instead of a single IM.
- `CUSTOM_FEED_URLS` and `NV_IM_*_WEBHOOK` configuration documented in `.env.example`.

## 0.5.2 — Verity (2026-11-17)

### Added
- `app/verification/source_policy.py`: strict whitelist covering the Top 30 media, professional fact-checkers, globally recognised search engines and authoritative primary sources.
- `/api/source-policy` and `/api/v1/source-policy` expose the complete allow-list and deny-list; a new dashboard panel makes the policy auditable.
- `scripts/clean_untrusted_sources.py` removes historical non-whitelisted sources and linked evidence (dry-run by default).

### Changed
- Evidence collection now rejects Baidu Baike/Wenku, QQ, Sohu, Huxiu, Wikipedia and other aggregator or encyclopedia domains before fetching and persistence.
- Top 30 cross-check links pass through the same whitelist filter.
- Event details label each evidence item with its source type; the methodology panel documents the policy.

## 0.5.1 — Atlas (2026-11-17)

### Fixed
- Runtime JavaScript failure caused by Python escape sequences being consumed inside the embedded HTML string, which made every dashboard button dead after deployment.
- Rewrote the nested `onclick` in `showTrackSettings()` with HTML entities so quotes are unambiguous.

### Added
- A rendered-HTML JavaScript validation step using `ast.literal_eval` plus `node --check`, so source-level checks can no longer miss runtime-only syntax errors.

## 0.5.0 — Atlas (2026-11-17)

### Added
- Four switchable page templates: **Aurora** (default dark), **Paper** (light), **Slate** (professional dark), **Terminal** (high-contrast monospace). Selection is persisted in `localStorage`.
- Top navigation bar, version chip and a **Version & Updates** modal with release history and theme preview.
- Unified version module `app/version.py`; `/api/version` and `/api/v1/version` expose version, themes and release notes.
- Complete software documentation in English, Chinese and Japanese: `README.md`, `README.zh-CN.md`, `README.ja.md` and `docs/SOFTWARE.{en,zh-CN,ja}.md`.
- `scripts/sync_github.sh` to publish every release to GitHub with one command.
- `.gitignore` to prevent `.env` and local build artifacts from being committed.

### Changed
- Replaced hard-coded dashboard colors with semantic CSS variables, so all templates share one component structure.
- Header now shows the real version and links to tri-language documentation.
- `compose.yaml` image tag and `pyproject.toml` version aligned to `0.5.0`.
- Redacted API key from previously published update notes.

### Fixed
- NAS runtime was still serving an older `app.py` and `top_media.py`; both are now synchronized and the stack rebuilt.

## 0.4.0 — Signal (2026-11-17)

### Added
- Top media expanded from 10 to 30, with lit/gray reporting state, report counts and clickable sources.
- Two independent task-card actions: tracking status summary and tracking settings.
- System status panel with CPU, memory, disk, process RSS, uptime and live external API probes.
- LLM primary/backup endpoint failover with endpoint-level circuit breaking.

### Fixed
- Broken `renderEvents()` template literal that caused an empty task list and dead buttons.
- Zombie `running` jobs recovered on worker startup.
- Telegram token failure no longer crashes the worker.
- Event detail 500 caused by a non-existent `Notification.created_at` field.
