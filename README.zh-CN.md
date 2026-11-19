# NewsVerify

**自建、可审计的新闻事实核查工作台。** 版本 **0.8.0（Vault）** · 2026-11-19。

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

## 0.8.0 新变化

- 全新 **NVDS 设计框架**：统一设计令牌、玻璃质感顶栏、氛围背景、组件库与动效，九套主题贯穿控制台、登录注册、后台与 API 页面。
- 登录改为**用户名 + 4 位 PIN**；新增独立的邀请码注册页（用户名 + 4 位 PIN + 6 位邀请码）、签名会话与退出登录。内置超级管理员：`caishen/1314`、`kayla/0720`。
- 超级管理员可批量生成邀请码，设置类别、次数与有效期，并一键复制带注册地址的使用说明。
- 新增**管理 Key 体系**（read/write/admin 权限、调用计数）与运行时 API 设置；新增查询接口与全过程资料、脑图模型接口。
- 新增 **`/admin/api` 控制台**：接口目录、在线调试、自动生成 cURL/Python/JS 代码与可复制的 Agent 系统提示词。

## 0.7.3 新变化

- **真正连线的脑图**：中心新闻通过带箭头的彩色 SVG 贝塞尔曲线连向六大维度，再连到每条主张、来源与记录；三种布局（树形 / 瀑布 / 放射）可随时切换并记住选择。
- **每条新闻后面都有自己的脑图**：任务卡片内嵌专属迷你脑图，点开即进入完整脑图；事件详情内也内嵌可交互脑图。可生成匿名只读分享链接与二维码，也可导出 SVG / PNG。

## 0.7.2 新变化

- **交互式追踪脑图**（🧠）：全景一屏查看所有新闻；点进任一新闻展开可折叠脑图，涵盖主张与判定、证据溯源、媒体覆盖、持续追踪、处理进度、任务历史六大分支。追踪更新记录改为可读摘要，不再只显示哈希。
- **全面 bug 修复**：提交时选的更新频率现在真正创建订阅；进度时间线在任务完成后不再消失；「持续追踪」节点正确点亮；切换视图不再被轮询覆盖；追踪通知广播到所有已配置 IM 渠道；并修复 Top30 查询、重新核查、v1 追踪去重与弹窗转义等问题。

## 0.7.1 新变化

- **理论页 `/theory` 全面重做**：新增「如何判断一条新闻真实性」的四层理论全景（哲学 / 认知 / 方法 / 机构），以及「每条理论用在本系统哪一部分」的映射表。
- **所有引用逐条核实并附原文地址**：正文 `[1]`–`[17]` 编号引用可跳转到文末注释，列出原文链接（arXiv / ACL / DOI / 官方页）、最早发表机构、年份与理论依据，包含 Hovland & Weiss 1951（信源可信度）、Nickerson 1998（确认偏误）等奠基研究。
- **修正旧页错误的论文出处**（FEVER、AVeriTeC、trafilatura），并把体系图重绘为五层结构。

## 0.7.0 新变化

- **交互式 IM 接入向导** `/admin/im`：11 个主流平台四步接入（官方凭证 → 填表 → 扫码/回调 → 测试），参考 AstrBot / NoneBot / Koishi 的适配器向导设计。
- **无需写代码、无需重启**：凭证存数据库、页面回显自动脱敏、保存即生效。Telegram 支持扫码绑定；飞书/钉钉/企业微信/LINE/QQ OneBot 提供官方扫码入口与接收地址一键复制。
- 背景音乐扩展为 **20 种声景**，点一下播放、再点停止，面板 5 秒无操作自动淡出。

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
