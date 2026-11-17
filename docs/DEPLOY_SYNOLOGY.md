# Deploy on Synology NAS (N150-P)

## Prerequisites
- Docker + Compose available (DSM Container Manager).
- New isolated directory: /volume2/docker/newsverify (do not touch existing services).

## Steps
1. Copy project to /volume2/docker/newsverify.
2. Create .env from .env.example; fill TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_IDS, LLM_*, POSTGRES_*.
   chmod 600 .env
3. Build & start:
   sudo docker compose up -d --build
4. DB tables auto-created on startup (init_db).
5. Verify:
   curl http://127.0.0.1:8080/health
   curl http://127.0.0.1:8080/api/status
6. Logs: sudo docker compose logs -f bot worker

## Backup
- scripts/backup.sh (pg_dump gzipped).
- Restore: gunzip + psql.

## Update
- git pull / scp new tarball, rebuild with --no-cache if needed.

## Web UI
- Published on host port 8080 (0.0.0.0). For public access via Cloudflare Tunnel, add public hostname new.<domain> -> http://192.168.8.253:8080 in Cloudflare Zero Trust.