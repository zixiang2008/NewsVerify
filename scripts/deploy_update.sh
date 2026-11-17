#!/usr/bin/env bash
# NewsVerify 更新部署脚本（2026-11-17）
# 用法：把整个项目同步到 NAS 后，在 NAS 项目目录下执行：
#   bash scripts/deploy_update.sh
set -euo pipefail

cd "$(dirname "$0")/.."
echo "=== NewsVerify 更新部署 $(date '+%F %T') ==="

# 0. 前置检查
if [ ! -f .env ]; then echo "❌ 缺少 .env"; exit 1; fi
echo "当前 LLM 配置:"
grep -E '^LLM_(BASE_URL|BASE_URL_FALLBACK|MODEL)=' .env || true

# 1. 备份数据库（在重建前）
echo "==> 备份数据库..."
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p backups
if docker compose ps db | grep -q "Up"; then
  docker compose exec -T db pg_dump -U "${POSTGRES_USER:-newsverify}" "${POSTGRES_DB:-newsverify}" \
    | gzip > "backups/newsverify-preupdate-${TS}.sql.gz" && echo "✅ 备份完成: backups/newsverify-preupdate-${TS}.sql.gz"
else
  echo "⚠️ db 未运行，跳过备份"
fi

# 2. 重建并启动
echo "==> 重建容器（拉取最新代码镜像）..."
docker compose up -d --build

# 3. 等待服务就绪
echo "==> 等待服务就绪..."
for i in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:8095/health >/dev/null 2>&1; then
    echo "✅ 服务已就绪"; break
  fi
  sleep 3
done

# 4. 验证前端 JS 已更新（新版本应含 loadSystem）
echo "==> 验证前端..."
PIN=$(grep -oE '^PIN_CODE ?= ?"[0-9]+"' app/web/app.py | grep -oE '[0-9]+' || echo "1314")
JS_OK=$(curl -fsS -c /tmp/nv_pin_cookie -X POST -d "pin=${PIN}" http://127.0.0.1:8095/login >/dev/null 2>&1 && \
        curl -fsS -b /tmp/nv_pin_cookie http://127.0.0.1:8095/ | grep -c "loadSystem" || echo "0")
if [ "${JS_OK}" -gt 0 ]; then
  echo "✅ 前端已更新（系统运行状况面板存在）"
else
  echo "⚠️ 前端似乎未更新，请检查 PIN 或镜像缓存"
fi

# 5. 提示清理历史失败任务
echo ""
echo "==> 如需清理历史失败任务（16 个旧 API 导致的 failed），执行："
echo "    docker compose exec bot python scripts/clean_failed_jobs.py        # 预览"
echo "    docker compose exec bot python scripts/clean_failed_jobs.py --apply  # 执行"
echo ""
echo "🎉 部署完成。打开首页登录后，页面下方可见「系统运行状况」面板。"
