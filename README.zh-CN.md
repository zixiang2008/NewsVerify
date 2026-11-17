# NewsVerify

**自建、可审计的新闻事实核查工作台。** 版本 **0.5.2（Verity）** · 2026-11-17。

NewsVerify 会把一段新闻拆成可核查主张，检索开放网络证据，判断来源独立性，输出受约束的六类判定，与 30 家高公信力媒体交叉验证，并持续追踪事件的实质变化。

- 公网入口：https://new.caishen.today
- 局域网入口：`http://192.168.8.253:8095`
- 源码：https://github.com/zixiang2008/NewsVerify

## 从哪开始

| 文档 | 语言 | 用途 |
| --- | --- | --- |
| [README.md](README.md) | English（默认） | 快速开始与文档导航 |
| [README.zh-CN.md](README.zh-CN.md) | 简体中文 | 快速开始与文档导航 |
| [README.ja.md](README.ja.md) | 日本語 | クイックスタートと文書案内 |
| [docs/SOFTWARE.en.md](docs/SOFTWARE.en.md) | English | 完整软件说明（英文） |
| [docs/SOFTWARE.zh-CN.md](docs/SOFTWARE.zh-CN.md) | 中文 | 完整软件说明书 |
| [docs/SOFTWARE.ja.md](docs/SOFTWARE.ja.md) | 日本語 | ソフトウェア仕様書 |
| [docs/PROJECT.md](docs/PROJECT.md) | 中文 | 架构、数据模型与部署细节 |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | English | 六体系与判定规则 |
| [docs/API.md](docs/API.md) | English | Public API v1 参考 |
| [CHANGELOG.md](CHANGELOG.md) | English | 版本历史 |

详细阅读建议：先读 [完整软件说明书](docs/SOFTWARE.zh-CN.md)，再按需要用 [PROJECT.md](docs/PROJECT.md) 查架构与部署细节。

## 0.5.2 新变化

- **严格可信来源白名单**：证据池只收录全球公信力靠前的媒体、专业事实核查机构、国际搜索引擎入口与权威一手资料机构。
- 百度百科/文库、QQ、搜狐、虎嗅、维基百科等聚合站与百科站在检索阶段即被拒绝，不再进入证据池。
- 每条证据标注来源类型；新增「可信来源白名单」面板与 `/api/source-policy` 接口，白名单可审计。
- 新增 `scripts/clean_untrusted_sources.py`，可清理历史遗留的非白名单来源（默认 dry-run）。

上一版 0.5.1 增加了 4 套可切换页面风格（极光/纸张/石墨/终端）、顶部导航、版本徽标、版本弹窗、统一版本管理、三语说明与 GitHub 同步。

完整历史见 [CHANGELOG.md](CHANGELOG.md)。

## 群晖 NAS 快速开始

```bash
cd /volume2/docker/newsverify
cp .env.example .env && chmod 600 .env
DOCKER=/volume2/@appstore/ContainerManager/usr/bin/docker
$DOCKER compose up -d --build
curl http://127.0.0.1:8095/health
curl http://127.0.0.1:8095/api/version
```

容器内访问 NAS 本机 LLM 服务时，请使用 Docker 网关地址，例如 `http://172.17.0.1:3065/v1`。配置模板见 `.env.example`，切勿提交 `.env`。

## 三种入口

- **网页：** 输入 PIN，粘贴文本或链接，选择模式和追踪频率，查看实时节点时间线与 30 家媒体覆盖图。
- **Telegram：** `/check`、`/deep`、`/track`、`/untrack`、`/status`、`/history`、`/privacy`。
- **API v1：** `/api/v1/` 下使用 `X-API-Key` 鉴权的端点。

## 技术栈

Python 3.12 · FastAPI · aiogram · SQLAlchemy asyncpg · PostgreSQL 16 · OpenAI 兼容 LLM（主备切换）· ddgs/Brave/SearXNG 搜索 · trafilatura 抽取 · Docker Compose。

## 安全与边界

PIN 登录、可选 API Key、外部 URL 的 SSRF 校验、独立性去重与受约束判定标签，共同降低误判风险。NewsVerify 是决策辅助工具，不是法律或专业裁决机构；结果是某一时刻的快照，持续追踪正是为事实变化而设计。

## 发布流程

1. 更新 `app/version.py`、`pyproject.toml`、`compose.yaml`、`CHANGELOG.md`；
2. 更新英 / 中 / 日三语文档；
3. 运行 `./scripts/sync_github.sh` 推送脱敏源码；
4. 部署到 NAS，验证 `/health`、`/api/version` 和页面版本徽标。
