# Changelog

All notable changes to NewsVerify are documented here. The current version is **0.5.1 (Atlas, 2026-11-17)**.

The single source of truth for the version is [`app/version.py`](app/version.py). Web UI, API, `pyproject.toml`, `compose.yaml` and documentation all follow it.

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
