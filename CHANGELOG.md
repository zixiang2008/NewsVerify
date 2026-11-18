# Changelog

All notable changes to NewsVerify are documented here. The current version is **0.7.3 (Canvas, 2026-11-19)**.

The single source of truth for the version is [`app/version.py`](app/version.py). Web UI, API, `pyproject.toml`, `compose.yaml` and documentation all follow it.

## 0.7.3 — Canvas (2026-11-19)

- Rebuilt the mind map as a real graph: a central news node connects via coloured SVG bezier links (with arrowheads) to six dimensions and then to individual claims, sources and records. The old card stack had no visible connectors.
- Added three switchable layouts — **tree** (left→right), **waterfall** (top→down) and **radial** (circular) — with local persistence; the same engine powers the console, the per-news detail map and the public share page.
- Every news card now carries its own mini mind map directly behind it; clicking it opens that news item's full six-dimension map. The event detail modal also embeds an interactive map.
- Added mind-map sharing: an anonymous read-only snapshot link plus QR code; recipients need no login and can switch layout/theme and download SVG or PNG.
- Toolbar: expand/collapse branches, zoom, layout switch, share, SVG/PNG export, plus a six-colour legend and short reading hint.
- Fixed the old expand/collapse state logic (it worked in reverse) and the zero-height pseudo-element that made connections invisible.
- Full-chain re-verification: Python compilation, rendered-JS syntax, three-layout geometry/link generation, share-page script, API routes and public access paths.

## 0.7.2 — Lens (2026-11-18)

- Added the interactive **Tracking Mind Map** (`🧠`): an overview screen shows every news item at a glance; opening one renders a mind map centred on that story with six collapsible branches — claims & verdicts, evidence & provenance, media coverage, continuous tracking, processing progress, and job history.
- Mind map supports expand/collapse all, node drill-down, and a root node that jumps straight to full detail; entry points added to both the tracking-status and event-detail views.
- Tracking update records now show readable summaries (evidence change / number of sources / "tracking started") instead of bare hash fingerprints.
- Fixed: the update frequency chosen at submission (`freq`) was never turned into a subscription — the worker now creates/upserts it idempotently once the check completes.
- Fixed: the worker's final `job.result` write overwrote the accumulated `progress`, emptying the progress timeline after completion.
- Fixed: the list card's "continuous tracking" node had `subs` hard-coded to `0` and never lit up (API now returns `active_subs`).
- Fixed: the detail-view polling timer was not stopped on view switch, forcibly overwriting tracking/settings/mind-map views.
- Fixed: tracking notifications were only sent to `chat_id=0` (always failing for web subscriptions) and skipped configured IM channels — now broadcast to all configured channels.
- Fixed: Top-30 supplementary queries used an uncomputed `hit_count` for emptiness checks; `recheck` used the truncated title and lost the original text; v1 track inserted duplicate subscriptions.
- Fixed: several unescaped fields in the detail modal that could break layout or allow injection; per-claim media coverage now includes clickable source links.

## 0.7.1 — Source (2026-11-18)

- Rebuilt the public `/theory` page: added a four-layer "how to judge a news story's truth" overview (philosophy / cognition / method / institutions) and a theory-to-implementation mapping table showing exactly which theory powers which part of the system.
- All in-text citations are now numbered `[1]`–`[17]` and link to a full source-notes section listing the original URLs (arXiv / ACL Anthology / DOI / official pages, all sources where multiple exist), the earliest publishing institution, year, and the theoretical basis of each source.
- Fixed incorrect paper references in the old page: FEVER → arXiv:1803.05355 (NAACL 2018), AVeriTeC → arXiv:2305.13117 (NeurIPS 2023), trafilatura → ACL 2021.acl-demo.15.
- Redrew the system diagram as five layers (theory → method → rating studies → pipeline → output) with citation numbers on each node.

## 0.7.0 — Bridge (2026-11-17)

### Added
- Interactive IM onboarding wizard at `/admin/im` covering 11 mainstream platforms in four guided steps (official credentials → form → QR/callback → test), modelled on the adapter-driven WebUI wizards of AstrBot / NoneBot / Koishi.
- Database-backed credential store (`im_channel_configs`): settings saved from the web wizard take effect immediately and survive restarts; values are masked on read, so no `.env` editing and no container restart are required.
- QR binding: Telegram deep-link QR with `/start` polling; official scan-entry guidance and one-click inbound-URL copy for Feishu / DingTalk / WeCom / LINE / QQ OneBot.
- Per-platform outbound message formats for real test messages (Feishu/DingTalk signing, WeCom, Discord, Slack, LINE, Matrix, Telegram); test results are recorded on each channel.
- `segno` QR dependency and 15 automated onboarding-logic checks.

### Changed
- Admin console now links prominently to the guided wizard; the old channel table remains as a read-only overview.

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
