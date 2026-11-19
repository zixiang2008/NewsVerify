# NewsVerify API

Base URL: `https://new.caishen.today` (LAN: `http://192.168.8.253:8095`)

All `/api/v1/*` calls require a management key: header `X-API-Key: <key>` or query `?api_key=<key>`.

Keys are created by a super administrator in `/admin/api`; scopes are `read`, `write`, `admin`. Read keys may call `GET`; write keys may also call `POST/PUT/PATCH/DELETE`. The legacy `API_KEY` environment variable remains a valid fallback. Runtime switches in `/admin/api` can disable the API entirely or block write operations.

## Agent quick start

```bash
curl -H "X-API-Key: $NV_KEY" https://new.caishen.today/api/v1/keys/me
```

1. Validate the key with `/api/v1/keys/me`.
2. `POST /api/v1/check` with `{"text":"...","mode":"full","freq":"none"}` → `event_id`, `job_id`.
3. Poll `GET /api/v1/jobs/{job_id}` until `status` is `done` or `failed`.
4. `GET /api/v1/events/{event_id}/process` for the full evidence chain and verdicts.
5. `GET /api/v1/events/{event_id}/mindmap?layout=radial` for a render-ready mind-map model.

Copy-ready cURL / Python / JavaScript samples and an Agent system prompt are generated in `/admin/api`.

## Public API v1

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/status` | Service status, counters and version |
| GET | `/api/v1/version` | Version, codename, themes, release history |
| GET | `/api/v1/top-media` | Top 30 credible media list |
| GET | `/api/v1/source-policy` | Trusted-source whitelist |
| GET | `/api/v1/keys/me` | Validate key; show name, scopes and masked prefix |
| POST | `/api/v1/check` | Submit news; body `{"text","mode","freq"}` → `{"event_id","job_id"}` |
| GET | `/api/v1/query/news` | Search events: `q`, `status`, `limit` |
| GET | `/api/v1/events` | Recent 50 events with latest verdicts |
| GET | `/api/v1/events/{id}` | Detail: claims, verdicts, evidence, media, jobs, subscriptions |
| GET | `/api/v1/events/{id}/process` | **Full process record**: progress timeline, claims, verdicts, evidence with source metadata, notifications, job history, mind-map model |
| GET | `/api/v1/events/{id}/mindmap` | Six-branch mind-map JSON; `layout=tree\|waterfall\|radial` |
| GET | `/api/v1/jobs/{id}` | Job payload, result, progress, attempts and errors |
| POST | `/api/v1/track/{id}` | Idempotent tracking; body `{"interval":"6h\|24h\|week"}` |
| POST | `/api/v1/untrack/{id}` | Disable tracking |
| DELETE | `/api/v1/events/{id}` | Delete event and all related records |
| POST | `/api/v1/im/{channel}/webhook` | Unified inbound webhook for IM platforms |

`GET /api/v1/events/{id}/process` returns `{"detail": {...}, "mindmap": {...}}`. `detail` contains `jobs[].progress`, `claims[].verdict`, `claims[].evidence[]` (URL, domain, `source_type`, `media_rank`, `media_name`, timestamps), `top_media`, `subscriptions` and `notifications`.

## Session-authenticated console endpoints

Console and admin endpoints use signed account cookies (`nv_auth` / `nv_admin`), not API keys.

### Account
- `GET /login`, `POST /login` — `username` + 4-digit `pin`
- `GET /register`, `POST /register` — `username`, `pin`, 6-digit `code`
- `GET /logout` — clear both sessions
- `GET /admin/login`, `POST /admin/login` — super admins only

### Admin (super admin session)
- `GET /api/admin/config` — masked API configuration
- `GET /api/admin/users` — user accounts
- `GET /api/admin/invites` — invitation codes
- `POST /api/admin/invites/generate` — `{"count","role","note","max_uses","expires_days"}` → codes, URLs and share text
- `DELETE /api/admin/invites/{code}` — revoke a code
- `GET /api/admin/api-keys` — managed keys
- `POST /api/admin/api-keys` — `{"name","scopes":["read","write","admin"]}` → full key (shown once)
- `PATCH /api/admin/api-keys/{key}` — `{"enabled","name","scopes"}`
- `DELETE /api/admin/api-keys/{key}` — revoke key
- `GET /api/admin/api/settings` — runtime API settings and defaults
- `PUT /api/admin/api/settings` — `{"api_enabled","allow_write","max_results","rate_limit_per_min","public_base_url","agent_note"}`
- `GET /api/admin/channels`, `/api/admin/channels/guide`, `/api/admin/channels/{key}/qrcode`, `/api/admin/channels/{key}/bind-status`
- `POST /api/admin/channels/{key}/config`, `DELETE /api/admin/channels/{key}/config`, `POST /api/admin/channels/{key}/test`

### Console
- `GET /api/version`, `/api/source-policy`, `/api/system`, `/api/events`, `/api/events/{id}`
- `POST /submit`, `/api/track/{id}`, `/api/track/{id}/settings`, `/api/untrack/{id}`, `/api/recheck/{id}`
- `POST /api/mindmap/share`, `DELETE /api/mindmap/share/{token}`

## Public mind-map sharing
- `GET /share/{token}` — read-only page with layout/theme switching and SVG/PNG export
- `GET /api/mindmap/share/{token}` — snapshot JSON
- `GET /api/mindmap/share/{token}/qrcode` — SVG QR code

## Pages
- `/` — verification console (account session)
- `/login`, `/register`, `/admin/login` — account entry points
- `/admin`, `/admin/accounts`, `/admin/api`, `/admin/im` — super-admin consoles
- `/theory` — public theoretical-sources page
- `/health` — public health probe

## OpenAPI
Machine-readable spec: `https://new.caishen.today/openapi.json`; interactive docs: `/docs`.
