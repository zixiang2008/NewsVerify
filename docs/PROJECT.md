# NewsVerify 项目说明

> 个人新闻事实核查与追踪服务，部署在群晖 NAS（N150-P）上，通过 Telegram Bot 与网页双入口使用。
> 域名：`new.caishen.today`（Cloudflare Tunnel 公网入口）；局域网入口：`http://192.168.8.253:8095`。
> 软件版本：0.7.0（Bridge） · 文档更新：2026-11-17

---

## 目录

1. [项目定位](#1-项目定位)
2. [核心原理](#2-核心原理)
3. [系统架构](#3-系统架构)
4. [目录结构](#4-目录结构)
5. [核查流水线](#5-核查流水线)
6. [判定标签与证据规则](#6-判定标签与证据规则)
7. [数据模型](#7-数据模型)
8. [三种使用入口](#8-三种使用入口)
9. [系统运行状况面板](#9-系统运行状况面板)
10. [外部 API 配置](#10-外部-api-配置)
11. [部署与运维](#11-部署与运维)
12. [2026-11-17 修复记录](#12-2026-11-17-修复记录)

---

## 1. 项目定位

NewsVerify 是一个"输入一段新闻/说法 → 输出结构化事实核查结论"的自建服务。它不做简单关键词匹配，而是模拟人工核查流程：

- 把一段文本**拆成可核查的独立主张**（claim）；
- 为每条主张**联网检索证据**，并标记证据的立场（支持/反驳/中性）与来源独立性；
- 由大模型（LLM）**综合证据给出判定标签和置信度**，并写出理由、反证和证据缺口；
- 用 **Top 30 全球公信力媒体交叉验证**（按 MBFC 事实报道等级 + 编辑独立性排序）；
- 对已核查事件提供**持续追踪**，检测到新证据时推送更新，并支持独立的频率/时间设置。

设计原则：**宁可判"证据不足"，也不在没有证据时说"支持"**；不编造媒体评级（六大评级体系只做元数据记录，未接入的不伪造分数）。

---

## 2. 核心原理

### 2.1 六阶段核查方法论

| 阶段 | 说明 |
| --- | --- |
| ① 主张拆分 | 从文本中抽取一条条可独立验证的事实主张 |
| ② 证据检索 | 对每条主张联网搜索，抓取正文，按来源去重 |
| ③ 独立性判定 | 用 `independence_chain_id` 标记同源/转载，避免"多家报道=多份证据"的假象 |
| ④ LLM 判定 | 基于证据输出标签、置信度、理由、反证、证据缺口 |
| ⑤ 六体系元数据 | 记录 NewsGuard / Ad Fontes / AllSides 等评级状态（未接入标注 not_connected，不伪造） |
| ⑥ 持续追踪 | 按 6h/24h/周 定期复查，内容指纹变化时通知订阅者 |

### 2.2 防幻觉与防误判机制

- **强制证据**：判定提示词明确要求"无证据不得判 supported"。
- **标签白名单**：LLM 返回的标签必须在六种合法标签内，否则降级为 `insufficient_evidence`。
- **来源独立性**：同源转载只算一份证据权重。
- **SSRF 防护**：所有外部 URL 抓取前做内网地址/协议校验，防止被诱导访问内网。
- **内容指纹**：`content_hash` / `snippet_hash` 用于检测证据与追踪内容是否真变化。

---

## 3. 系统架构

三个容器组成一个 Docker Compose 栈（网络 `newsverify`，独立数据卷）：

```
                    ┌─────────────────────────────┐
   Telegram  ──────► │  bot 容器 (APP_MODE=all)     │
   用户消息          │  · aiogram 长轮询            │
                    │  · FastAPI Web UI :8095      │  ◄── 浏览器 / Agent
                    │  · 提交任务写 jobs 表         │
                    └──────────────┬──────────────┘
                                   │ 写 jobs / 读 events
                    ┌──────────────▼──────────────┐
                    │  worker 容器 (APP_MODE=worker)│
                    │  · 消费 jobs                  │
                    │  · 完整核查流水线             │
                    │  · 结果写回 + Bot 推送         │
                    └──────┬──────────────┬────────┘
                           │              │
              ┌────────────▼───┐   ┌──────▼────────────────┐
              │ db 容器         │   │ 外部服务              │
              │ PostgreSQL 16   │   │ · LLM 主/备 API       │
              │ (pgdata 卷)     │   │ · 联网搜索(yahoo/DDG)  │
              └────────────────┘   │ · Telegram Bot API    │
                                   └───────────────────────┘
```

- **异步解耦**：Web/Bot 只负责提交与展示，重活交给 worker 后台消费 `jobs` 表。
- **高可用 LLM**：LLM 客户端内置主备端点自动切换 + 熔断，主 API 超时/报错时自动走备用。
- **优雅降级**：Telegram token 失效时 worker 不再崩溃，改为"照常核查、跳过推送"。
- **僵尸回收**：worker 启动时会把超过 10 分钟仍卡在 `running` 的任务重置为 `queued`，避免重启后任务永久卡死。

---

## 4. 目录结构

```
NewsVerify/
├── .env                      # 实际配置（含密钥，勿外泄，chmod 600）
├── .env.example              # 配置模板（含全部键与说明）
├── .gitignore                # 防止 .env / 缓存 / 构建产物进入 Git
├── Dockerfile                # 应用镜像（bot/worker 共用）
├── compose.yaml              # 三容器编排（db / bot / worker）
├── pyproject.toml            # 依赖与项目元数据（Python ≥3.11，版本 0.6.1）
├── README.md                 # 默认英文入口与导航
├── README.zh-CN.md           # 中文入口与导航
├── README.ja.md              # 日文入口与导航
├── CHANGELOG.md              # 版本变更记录
├── app/
│   ├── main.py               # 进程入口：按 APP_MODE 启动 web/bot/worker
│   ├── version.py            # **版本号与更新记录的唯一来源**
│   ├── worker.py             # 任务消费与核查流水线编排
│   ├── bot/                  # Telegram 机器人（命令、键盘）
│   │   ├── handlers.py       # /check /deep /track /status 等命令
│   │   └── keyboards.py      # 内联按钮
│   ├── web/                  # FastAPI Web 应用
│   │   ├── app.py            # 路由 + 单页前端 + 后台/理论页路由
│   │   ├── system_status.py  # 系统运行状况采集（API 探测 + 资源）
│   │   └── theory.py         # /theory 理论来源专题页（公开）
│   ├── core/                 # 配置、日志、安全（API Key / SSRF / PIN）
│   ├── db/                   # 数据模型与异步会话
│   ├── ingest/               # 抓取与正文提取（平台适配、trafilatura）
│   │   └── open_web.py       # 合规公开信息采集（RSS/robots/限速）
│   ├── integrations/         # 多即时通讯接入适配层（config-driven）
│   ├── verification/         # 核查核心：主张/搜索/证据/判定/LLM/Top媒体
│   │   └── source_policy.py  # 可信来源白名单（允许类别 + 显式拒绝表）
│   ├── ratings/              # 六大评级体系元数据
│   └── tracking/             # 追踪差分（内容指纹比对）
├── docs/
│   ├── SOFTWARE.en.md        # 完整软件说明（英文）
│   ├── SOFTWARE.zh-CN.md     # 完整软件说明（中文）
│   ├── SOFTWARE.ja.md        # 完整软件说明（日文）
│   ├── PROJECT.md            # 本文档（完整项目说明）
│   ├── METHODOLOGY.md        # 核查方法论
│   ├── API.md                # Public API v1 参考
│   ├── DEPLOY_SYNOLOGY.md    # 群晖部署要点
│   └── UPDATE-2026-11-17.md  # 修复与升级记录
├── scripts/
│   ├── deploy_update.sh      # 部署/更新（含清理与重建）
│   ├── sync_github.sh        # 一键提交并推送脱敏源码到 GitHub
│   ├── clean_failed_jobs.py  # 清理历史失败任务（默认 dry-run）
│   ├── clean_untrusted_sources.py  # 清理非白名单历史来源（默认 dry-run）
│   ├── backup.sh             # 数据库备份（pg_dump 压缩）
│   ├── preflight.sh          # 部署前检查
│   └── smoke-test.sh         # 冒烟测试
└── tests/                    # 单元测试
```

---

## 5. 核查流水线

提交一条任务后，worker 按以下顺序处理，并把每一步进度写入 `jobs.result.progress` 供前端实时展示：

1. **收到任务，开始核查** —— job 从 `queued` → `running`。
2. **主张拆分** —— 调用 LLM 把文本拆成 N 条独立主张（受 `MAX_CLAIMS_PER_CHECK` 限制）。
3. **证据检索** —— 对每条主张调用搜索 + 抓取正文，生成 Source 与 Evidence。
4. **证据持久化** —— 先 flush Source 再建 Evidence，避免外键约束错误。
5. **LLM 判定** —— 每条主张输出标签、置信度、理由、反证、缺口。
6. **Top 30 媒体交叉核查** —— 遍历 30 家高公信力媒体做 `site:` 搜索（此步最慢），逐条主张记录哪些媒体有报道及来源链接。
7. **写库并提交事务** —— 全部完成后一次性 commit，随后 Bot 推送结果。

> 前端"任务状态"里看到的主张/证据在任务完成前可能显示为 0，是因为数据在事务里、最后才 commit；这是正常现象，进度时间线会实时更新。

---

## 6. 判定标签与证据规则

六种合法标签：

| 标签 | 含义 |
| --- | --- |
| `supported` | 有充分证据支持 |
| `refuted` | 有充分证据反驳 |
| `mixed` | 证据支持与反驳并存 |
| `insufficient_evidence` | 证据不足/缺失（默认兜底） |
| `outdated` | 过去为真、现已变化 |
| `not_checkable` | 无法核查（如主观评价、未来预测） |

LLM 判定输出 JSON 结构：

```json
{
  "label": "supported",
  "confidence": 0.9,
  "rationale": "...",
  "counter_argument": "...",
  "evidence_gaps": ["..."],
  "cited_urls": ["..."]
}
```

---

## 7. 数据模型

| 表 | 作用 | 关键字段 |
| --- | --- | --- |
| `events` | 一次核查事件 | id, title, status, created_at |
| `claims` | 拆分出的主张 | id, event_id, text, language |
| `sources` | 证据来源 | url(unique), domain, content_hash, independence_chain_id, rating_status |
| `evidence` | 主张↔来源的证据 | claim_id, source_id, stance, snippet, snippet_hash |
| `verdicts` | 判定结果 | claim_id, label, confidence, rationale, counter_argument, evidence_gaps, model |
| `jobs` | 异步任务 | status(queued/running/done/failed), attempts, result, error |
| `subscriptions` | 追踪订阅 | event_id, chat_id, interval |
| `notifications` | 推送记录 | — |

所有子表通过外键 `ON DELETE CASCADE` 关联 `events`，删除事件时自动清理关联数据。

---

## 8. 三种使用入口

### 8.1 网页 UI（局域网 / 公网域名）

访问 `http://192.168.8.253:8095` 或 `https://new.caishen.today`，输入 PIN（默认见部署配置）登录。

- 顶部：提交框 + 模式（full/top10）+ 频率；提交后立即在任务列表顶部显示。
- 中部：任务列表（状态、判定标签、主张数、媒体报道覆盖数）。每个任务卡片有两个独立按钮：
  - **📡 追踪状态**：打开即汇总显示该新闻的活跃追踪、累计更新记录与检查时间；
  - **⚙️ 设置**：独立修改检查频率、下次检查时间、暂停状态，保存后更新追踪逻辑。
- 详情弹窗：进行中每 3 秒自动刷新，展示 6 大节点状态、进度时间线、完整核查结果、Top30 媒体覆盖（🟢 点亮/⚪ 灰色 + 可点开的来源链接 + 报道条数）。
- 右侧：Top30 媒体公信力榜，核查后按报道情况点亮/置灰，并汇总报道媒体数与来源数。
- 底部：**系统运行状况面板**（见第 9 节）。

### 8.2 Telegram Bot

命令：`/help /check /deep /track /untrack /status /history /privacy`，也可直接发文本或图片。

- `/check <文本>`：快速核查；`/deep <文本>`：深度核查。
- `/track <事件ID> [6h|24h|week]`：开启追踪。
- `/status`：查看任务状态。

### 8.3 Public API v1

需要 `API_KEY`（Header 鉴权）。主要端点：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/status` | 服务状态 |
| GET | `/api/v1/top-media` | Top30 媒体列表（含事实等级、独立性） |
| POST | `/api/v1/check` | 提交核查任务 |

> 注意：源码中 `pin_auth` 中间件会拦截 `/api/*`，因此 v1 实际需要 PIN cookie + API Key 双重鉴权。详见 `docs/API.md`。

---

## 9. 系统运行状况面板

页面底部面板，支持手动刷新按钮与每 30 秒自动刷新，数据来自后端 `/api/system`：

- **API 在线情况**：主 LLM、备 LLM、搜索服务（联网搜索）的名称、URL、在线状态、响应延迟；显示当前实际生效的端点（"生效中"标记）。
- **系统资源**：CPU 使用率、内存占用、磁盘占用、进程 RSS、运行时长、响应速度。

采集实现在 `app/web/system_status.py`，Linux 下读 `/proc`，macOS 下用 `sysctl` 兜底，不引入 psutil 依赖。

---

## 9.1 Top30 媒体榜单依据与来源借鉴

媒体列表定义在 `app/verification/top_media.py`，按"事实准确性 + 编辑独立性"综合排序，前 10 为全球通讯社/公共广播（Reuters、AP、AFP、BBC、NPR、PBS、DW、France24、NHK、ABC AU），其后为权威报纸、财经媒体、专业事实核查机构（Snopes、FactCheck.org、Politifact、Full Fact）与科学媒体。每家带 `factual`（MBFC 事实报道等级）、`independence`、`type` 字段。

**来源借鉴（2026-11-17 调研）：**
- **Media Bias/Fact Check（MBFC）**：覆盖 11000+ 媒体的事实报道/偏见分级（Very High / High / Mostly Factual），是本榜单事实性字段的参考。其数据 API 属商业/受限使用，本项目仅借鉴公开的分级口径，不调用其付费接口，也不伪造官方分数。
- **Reuters Institute《Digital News Report》**：公众信任度研究，用于排序参考。
- **Veracity（开源事实核查系统，arXiv:2506.15794）**：借鉴其"来源透明度三件套"（可靠性评分 + 解释 + 可追溯来源）与"来源独立性/多样性"理念。项目据此把独立性链 ID 改为基于正文指纹，避免"多家转载同一通稿"伪装成多份独立证据；并在结果里展示可点开的来源链接与报道条数。

**媒体状态呈现**：核查时对每条主张并发检查 30 家媒体（`site:domain + claim`），前端用 🟢 点亮（有报道）/ ⚪ 灰色（未见报道）表示，并显示"N 家媒体报道 / 共 M 条来源"，每条来源可点击打开原文。

---

## 10. 外部 API 配置

用户指定的外部 API（主/备自动切换）：

| 项 | 值 |
| --- | --- |
| 主 API | `http://172.17.0.1:3065/v1`（容器内走 Docker 网关；Mac 调试用 `192.168.8.253:3065`） |
| 备 API | `https://api.caishen.today:8443/v1` |
| Key | 已写入 `.env`，此处不公开密钥 |
| 模型 | `gemini-3-flash`（claim 与 judge 均用此模型；原 `auto/deepseek-v4-flash` 不存在，已弃用） |
| 搜索 | ddgs 库，实测 NAS 下 yahoo 后端最快最稳（无需密钥），失败退 duckduckgo |

> 容器内 `192.168.8.253:3065` 不通（超时），必须用 `172.17.0.1:3065`；两者指向 NAS 上同一个 3065 服务。LLM 客户端已实现主备切换，主端点熔断后自动走公网备用。

---

## 11. 部署与运维

### 11.1 环境

- 目标：群晖 N150-P，DSM 7.2.1，Container Manager（Docker Compose）。
- SSH：`ssh -i ~/.ssh/id_ed25519 caishen@192.168.8.253`（caishen 在 administrators 组，docker 免 sudo）。
- 部署目录：`/volume2/docker/newsverify`。
- 端口：Web `0.0.0.0:8095:8095`；公网经 Cloudflare Tunnel 映射 `new.caishen.today`。

### 11.2 部署步骤

```bash
# 在 Mac 上同步代码到 NAS（保留 NAS 的 .env）
rsync -av --exclude='.env' --exclude='__pycache__' --exclude='*.pyc' \
  /Volumes/OS2App/AiColding/NewsVerify/ \
  caishen@192.168.8.253:/volume2/docker/newsverify/

# 在 NAS 上执行
ssh -i ~/.ssh/id_ed25519 caishen@192.168.8.253
cd /volume2/docker/newsverify
DOCKER=/volume2/@appstore/ContainerManager/usr/bin/docker
$DOCKER compose up -d --build
$DOCKER compose logs -f bot worker
```

完整自动化脚本见 `scripts/deploy_update.sh`。

### 11.3 常用运维

| 操作 | 命令 |
| --- | --- |
| 查看容器 | `docker compose ps` |
| 查看日志 | `docker compose logs -f bot worker` |
| 重启 | `docker compose restart` |
| 备份数据库 | `bash scripts/backup.sh` |
| 清理失败任务 | `python scripts/clean_failed_jobs.py`（加 `--apply` 才真删） |
| 健康检查 | `curl http://127.0.0.1:8095/health` |
| 系统状态 | `curl -b cookie http://127.0.0.1:8095/api/system` |

### 11.4 注意事项

- **不要覆盖 NAS 的 `.env`**：其中含真实 Telegram token 与数据库密码。
- 数据库卷 `newsverify_pgdata` 独立于代码，重建容器不会丢数据。
- `.env` 的 `POSTGRES_PASSWORD` 必须与 `DATABASE_URL` 中的密码一致。

---

## 12. 2026-11-17 修复记录

本次修复了导致"后台有数据、前台全空、按钮点不动"的问题，并做了健壮性升级。完整清单见 `docs/UPDATE-2026-11-17.md`，摘要：

1. **前端致命语法错误**：`renderEvents()` 模板字符串提前闭合导致整个 `<script>` 解析失败，所有按钮失效、列表空白 —— 已修复并通过 `node --check`。
2. **渲染容错**：列表/详情逐条防御，单条脏数据不再让整页白屏。
3. **外部 API 切换**：主备自动切换 + 熔断；模型从不存在的 `auto/deepseek-v4-flash` 改为 `gemini-3-flash`。
4. **系统运行状况面板**：新增 `/api/system` 与前端面板。
5. **任务即时显示 + 节点内容**：提交后立即显示，详情定时刷新展示 6 大节点与完整结果。
6. **健壮性**：Bot token 失效时 worker 优雅降级；僵尸任务自动回收；LLM 超时与重试优化。
7. **历史故障清理**：提供 `scripts/clean_failed_jobs.py` 安全删除旧的 failed 任务。

### 2026-11-17 第二轮增强（同日）
8. **Top10 → Top30**：媒体榜单扩展到 30 家高公信力媒体，带 MBFC 事实等级/独立性字段；核查对每条主张并发检查全部 30 家，记录报道的来源链接与条数。
9. **媒体点亮/灰色**：右侧榜单与详情按报道状态用 🟢/⚪ 显示，展示"N 家媒体报道 / M 条来源"，来源可点击打开。
10. **追踪双入口**：任务卡片新增「📡 追踪状态」（汇总活跃追踪与所有更新记录）与「⚙️ 设置」（独立修改频率/下次时间/暂停）两个按钮；`/api/track` 支持更新已有订阅，`/api/track/{id}/settings` 处理设置变更。
11. **模块一致性审查**：独立性链 ID 改为基于正文指纹（防转载伪装）；媒体名次、评级来源在文档与代码中标注为"参考性榜单"，避免夸大描述。

---

## 13. v0.5.x：界面模板、版本体系与三语文档

### 13.1 多风格页面模板

前端不再只有一套深蓝样式。所有颜色改为语义化 CSS 变量（`--bg`、`--surface-*`、`--text`、`--muted`、`--border`、`--accent*`），四套模板只覆盖变量，不复制组件结构：

| 模板 | 定位 |
| --- | --- |
| 极光 Aurora | 默认深蓝玻璃质感 |
| 纸张 Paper | 浅色、阅读友好 |
| 石墨 Slate | 中性专业控制台 |
| 终端 Terminal | 高对比等宽字体 |

选择结果写入 `localStorage` 的 `nv_theme`，刷新后保留。页面顶部新增导航条、版本按钮和「版本与更新」弹窗；源码参考了 Tabler 的卡片网格与单包资源思路、GitHub Primer 的 CSS 变量主题令牌方法，但没有引入新的前端依赖，仍然内嵌在 `app/web/app.py` 中。

### 13.2 统一版本号

`app/version.py` 是唯一版本号来源，包含 `VERSION`、`RELEASE_DATE`、`CODENAME`、`THEMES`、`RELEASES`。Web 页面、登录页、`/api/version`、`/api/v1/status`、`pyproject.toml`、`compose.yaml`、README 与 CHANGELOG 都与之对齐。每次更新必须按第 7 节流程同步。

### 13.3 三语说明与 GitHub 同步

默认语言为英文，另有中文与日文；完整说明分别位于 `docs/SOFTWARE.en.md`、`docs/SOFTWARE.zh-CN.md`、`docs/SOFTWARE.ja.md`。`scripts/sync_github.sh` 会检查 `.env` 是否被忽略、在必要时初始化仓库、rebase 远端、按当前版本提交并推送到 `https://github.com/zixiang2008/NewsVerify`。

### 13.4 v0.5.1 运行时修复

首次部署后发现 `showTrackSettings()` 里的 `onclick` 因为 Python 三引号字符串吞掉反斜杠，导致整段 JS 在浏览器里解析失败、所有按钮失效。0.5.1 改用 HTML 实体 `&quot;` 避免引号嵌套，并增加“先按 Python 字符串求值、再用 `node --check` 校验”的检查方式，确保源码检查与运行时一致。

### 13.5 v0.5.2 可信来源白名单

线上事件详情里曾出现 `baike.baidu.com`、`wenku.baidu.com`、`news.qq.com`、`sohu.com`、`huxiu.com` 等来源。它们不是被写进 Top30 榜单，而是搜索引擎返回后未经筛选直接进入证据池。

0.5.2 新增 `app/verification/source_policy.py`，以严格白名单 + 显式拒绝表控制证据入口：

- **允许**：Top30 媒体及其权威变体域名、`FACTCHECK_DOMAINS`（Snopes / FactCheck.org / PolitiFact / Full Fact / AFP Fact Check / Lead Stories 等）、`SEARCH_ENGINE_DOMAINS`（Google / Bing / DuckDuckGo / Yahoo / Brave / Startpage）、`AUTHORITY_DOMAINS`（NASA / NOAA / WHO / UN / OECD 等）。
- **拒绝**：`BLOCKED_DOMAINS` 覆盖百度、QQ、搜狐、虎嗅、新浪、知乎、微博、维基百科、大英百科等聚合站/百科站/内容农场；子域名（如 `baike.baidu.com`）同样拒绝。
- **落点**：`collect_evidence()` 在抓取前过滤，`check_top_media()` 对展示来源再过滤；事件详情按 `classify_source()` 标注 `source_type`。
- **可审计**：`/api/source-policy` 与页面「可信来源白名单」面板公开完整名单；`scripts/clean_untrusted_sources.py` 可清理历史遗留数据（默认 dry-run，需 `--apply`）。

### 13.6 v0.6.0：界面扩展、接入层与理论页

- **9 套主题**：在原有 4 套基础上新增 ocean / forest / sunset / violet / mono，全部基于语义 CSS 变量，选择写入 `localStorage.nv_theme`。
- **背景音乐**：`MUSIC_TRACKS` + Web Audio 生成式振荡器（4 首氛围曲），可播放/停止/切换/调音量，无外部音频依赖；偏好写入 localStorage。
- **媒体面板**：`.media-list` 固定高度 + `overflow-y:auto` + 自定义滚动条；证据条目按 `media_rank / media_name / factual / reported_at` 渲染方括号标注，时间来自 Source 的 `published_at → fetched_at → created_at`。
- **合规采集**（`app/ingest/open_web.py`）：`parse_feed` 解析 RSS/Atom，`collect_google_news()` 用公开 RSS 搜索，`robots_allowed()` 检查 robots.txt，`_polite_wait()` 按域名限速；`enhanced_collect()` 汇入 `collect_evidence()` 的候选池，但仍经 `classify_source()` 白名单过滤。配置键 `CUSTOM_FEED_URLS`。
- **IM 接入层**（`app/integrations/`）：`BaseChannel` 抽象 + `TelegramChannel` + `GenericWebhookChannel`，`ChannelRegistry` 配置驱动注册 `CHANNEL_CATALOGUE`（含 11 种主流平台）；统一入口 `POST /api/v1/im/{key}/webhook`，每个平台用 `NV_IM_{KEY}_WEBHOOK` / `NV_IM_{KEY}_SECRET` 配置。设计参考 NoneBot/OneBot 与 Kirara AI 的适配器模式，但不引入其运行时依赖。
- **后台管理**：独立 PIN 会话 cookie `nv_admin`（PIN `1314`），路由 `/admin`、`/api/admin/config`（密钥脱敏）、`/api/admin/channels`、`/api/admin/channels/{key}/test`。中间件对 `/theory` 与后台登录放行。
- **理论页**：`app/web/theory.py` 的 `PAGE` 为自包含 HTML，公开访问 `/theory`，含方法论表、频段体系来源、SVG 体系图、逐条引用与学术评价。

### 13.7 v0.6.1：背景声景库与交互重构

- **20 种声景**：`app/web/app.py` 的 `MUSIC_TRACKS` 从 4 首扩展到 20 种，覆盖白噪音、颂钵、佛教庭院、室外鸟叫、细雨、雷雨、溪流、风铃、夏夜虫鸣、篝火、寺院钟声、月光、竹林、雪落等。每项声明 `layers`，由 `nvBuildLayer()` 按 `noise`（随机缓冲 + 双二阶滤波）、`pad`（振荡器 + 缓慢起伏）、`chirp`（随机频率扫描）、`strike`（泛音衰减敲击）四类合成，全部本地实时生成。
- **点击即播放**：`selectMusic(id)` 中，若当前正在播放同一 id 则 `stopMusic()`，否则 `startMusic(id)`；`startMusic()` 先 `nvDestroyLayers()` 再按新曲目的 layers 重建，因此切换曲目不会叠加声音。顶部按钮仍可打开/收起面板，面板底部保留统一播放/停止按钮。
- **5 秒自动淡出**：`.music-panel` 使用 `opacity + transform + transition`，`openMusicPanel()` 先设 `display:block` 再于下一帧加 `.show`，`closeMusicPanel()` 加 `.hide` 后 360ms 才 `display:none`；`resetMusicPanelHideTimer()` 由面板上的 `click/mousemove/input/wheel/touchstart` 事件重置，5 秒无操作触发淡出。淡出仅隐藏面板，`nvMusicOn` 不变，播放继续。
- **音量实时化**：`<input type=range oninput=...>` 替代原 `onchange`，`setMusicVolume()` 用 `setTargetAtTime` 平滑改主增益并显示百分比；曲目与音量分别持久化到 `nv_music_track` / `nv_music_vol`。
- **验证方式**：`ast` 提取 HTML 字面量 → 正则取 `<script>` → `node --check` 校验运行时脚本；另用 mock DOM/Web Audio 的 Node 脚本实测播放、停止、切换、音量、面板淡出逻辑。
