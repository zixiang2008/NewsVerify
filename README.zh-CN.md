# NewsVerify

**自建、可审计的新闻事实核查工作台。** 版本 **0.6.1（Echo）** · 2026-11-17。

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

## 0.6.1 新变化

- **背景音乐扩展为 20 种声景**（原为 4 首）：白噪音、颂钵、佛教庭院、室外鸟叫、下雨、雷雨、溪流、风铃、夏夜虫鸣、篝火、寺院钟声、竹林、雪落等，全部由 Web Audio 本地实时合成，无需外部音频文件。
- **点一下即播放**：再点一下停止，点其他声音自动切换；音量拖动时实时调节并显示百分比。
- 音乐面板 **5 秒无操作自动淡出**，也可手动关闭；淡出只收起面板，不中断播放。20 种声音在可滚动列表中全部可见。

## 0.6.0 新变化

- **9 套页面风格**（新增海洋/森林/日落/紫罗兰/素黑白）与**背景音乐**：4 首生成式氛围曲，可开关、可切换、可调音量。
- **30 家媒体面板**加入常驻滚动条；每条证据标题右侧方括号标注媒体名、全球可信榜名次、事实等级与报道时间。
- **合规公开信息采集增强**：RSS / Google News RSS 发现源，尊重 robots.txt、限速与重试，仍经可信来源白名单把关。
- **后台管理** `/admin`（PIN `1314`）：查看 API 配置，管理/测试主流即时通讯接入（Telegram、Discord、Slack、飞书、钉钉、企业微信、公众号、QQ/OneBot、LINE、Matrix、通用 Webhook）。
- 拓扑图简化为统一的「即时通讯工具」接入入口。
- 新增公开专题页 [理性查看新闻理论来源](docs/SOFTWARE.zh-CN.md)：方法论、可信度频段体系由来、图示、逐条引用出处与学术/全球评价。

上一版 0.5.2 增加了严格可信来源白名单、`/api/source-policy` 接口与历史数据清理工具。

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
