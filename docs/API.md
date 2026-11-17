# NewsVerify Public API

Base URL: `https://new.caishen.today`
Auth: header `X-API-Key: <key>` or query `?api_key=<key>`.

## Endpoints

- `GET /api/v1/status` — service status (includes `version`)
- `GET /api/v1/version` — version, release date, codename, themes and release history
- `GET /api/v1/top-media` — Top 30 credible media list
- `GET /api/v1/source-policy` — trusted-source whitelist (media / fact-checkers / search engines / authorities / blocked examples)
- `POST /api/v1/check` — submit news for verification
  body: `{"text": "...", "mode": "full|top30|method", "freq": "none|6h|24h|week"}`
  returns: `{"event_id", "job_id", "status": "queued"}`
- `GET /api/v1/events` — list events
- `GET /api/v1/events/{id}` — event detail with claims, verdicts, evidence, top_media, summary, jobs, subscriptions
- `POST /api/v1/track/{id}` — enable tracking (body `{"interval":"24h"}`)
- `POST /api/v1/untrack/{id}` — disable tracking
- `DELETE /api/v1/events/{id}` — delete event
- `POST /api/v1/im/{channel}/webhook` — unified inbound webhook for instant messengers (Telegram/Discord/Slack/Feishu/...). Set `X-API-Key` when `API_KEY` is configured.

## Console-only endpoints (PIN / admin session)
- `GET /api/version` — version, themes, release history
- `GET /api/source-policy` — trusted-source whitelist
- `GET /api/admin/config` — masked API configuration (admin PIN session)
- `GET /api/admin/channels` — IM connector catalogue and status
- `POST /api/admin/channels/{key}/test` — send a test reply through a webhook channel

## Pages
- `/` — verification console
- `/admin` — admin console (PIN `1314`)
- `/theory` — public "Rational News-Reading Theoretical Sources" page

## API Key
Provided separately. Keep secret. All requests require the key.

## OpenAPI
Interactive docs: `https://new.caishen.today/docs` (requires PIN login for browser; API key for calls).