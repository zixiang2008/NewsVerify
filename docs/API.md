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

## API Key
Provided separately. Keep secret. All requests require the key.

## OpenAPI
Interactive docs: `https://new.caishen.today/docs` (requires PIN login for browser; API key for calls).