# NewsVerify 软件说明书

**版本：** 0.7.2（Lens） · **发布日期：** 2026-11-18  
**代码仓库：** https://github.com/zixiang2008/NewsVerify  
**在线控制台：** https://new.caishen.today（局域网：`http://192.168.8.253:8095`）

本文档说明 NewsVerify 为什么存在、借鉴了哪些科研与评级资料、用什么论证方法从证据得出结论、所有数据源如何依据与组合，以及最近一次本地实验的结果。适合运维者、复核者以及需要理解或维护系统的 Agent 阅读。

---

## 1. 为什么要有这个软件

新闻、社交平台和生成式模型产出说法的速度，远远超过个人核查的速度。截图、转发和 AI 摘要可能同样“看起来很确定”，但证据基础完全不同。人工核查慢，关键词匹配不可靠，商业核查接口又不透明、无法部署到自己的机器上。

NewsVerify 因此被设计为一个**自建、可审计的说法核查工作台**。它不要求读者只相信模型的一句话，而是：

1. 把新闻拆成可独立验证的原子主张；
2. 为每条主张检索开放网络证据，并专门做反证导向查询；
3. 折叠通稿转载链，避免“很多家都这么说”被误当成独立多源；
4. 让大模型在六个固定标签中选择，并必须给出理由、反证和证据缺口；
5. 用 30 家高公信力媒体做交叉验证，保存可点开的来源链接；
6. 持续追踪事件，只有证据指纹真的变化时才通知。

设计原则是：**没有证据就说“证据不足”，绝不凭空说“支持”。**

---

## 2. 借鉴的科研资料与外部依据

NewsVerify 是多个公开研究与评级传统的工程综合。它不购买、不转售授权评级数据，也不伪造官方分数。

| 资料 | 贡献 | 在系统中的用法 |
| --- | --- | --- |
| FEVER 式主张核查 | 把文档拆成原子主张，分别检索支持/反驳证据 | `app/verification/claims.py`、`evidence.py` |
| AVeriTeC（真实世界主张核查） | 证据优先、显式记录证据缺口、保留不确定性 | 判定结构含 `evidence_gaps`、`counter_argument` 与六类标签 |
| Google Fact Check Tools API | 专业事实核查机构的 `textualRating` 与审核日期 | 配置密钥后由 `search_google_factcheck()` 作为官方补充置前 |
| Media Bias/Fact Check（MBFC） | 公开的“事实报道”分级：Very High / High / Mostly Factual | 作为 Top30 榜单 `factual` 字段的参考口径；不调用付费接口 |
| Reuters Institute《Digital News Report》 | 跨国家公众媒体信任度研究 | 作为媒体排序的背景依据，不充当单篇报道评分 |
| NewsGuard、Ad Fontes Media、AllSides | 可信度 / 偏见分类体系 | 在 `app/ratings/systems.py` 中标为 `not_connected`，未授权则不显示分数 |
| Pew Research、无国界记者组织 RSF | 受众行为与新闻自由环境 | 标为 `context_only`，提醒国家环境不等于事实真伪 |
| Veracity（arXiv:2506.15794）等开源系统 | 来源透明度三件套：可靠性 + 解释 + 可追溯链接；来源独立性 | 启发 `independence_chain_id`、可点来源列表与报道条数 |
| OpenAI 兼容 LLM API | 只基于检索证据做结构化推理 | 主备端点自动切换，输出受约束的 JSON 判定 |

六大评级体系元数据集中在 `app/ratings/systems.py`，每一项都写明授权状态。缺失的评级就显示为缺失，不猜测。

---

## 3. 用了什么论证方法，得出什么结论

### 3.1 六阶段核查流水线

| 阶段 | 操作 | 产物 |
| --- | --- | --- |
| ① 主张拆分 | LLM 把输入拆成受配置上限约束的原子主张 | `claims` |
| ② 证据检索 | 每条主张做原句查询 + 反证导向查询 | `sources` / `evidence` 候选 |
| ③ 独立性判定 | URL 去重 + 基于正文指纹的 `independence_chain_id`，折叠转载链 | 独立证据集 |
| ④ LLM 判定 | 只把证据片段交给结构化提示词 | 标签、置信度、理由、反证、缺口 |
| ⑤ 媒体交叉核查 | 宽搜索结果按域名匹配 Top30，少量重点媒体补 `site:` 查询 | 30 家点亮/灰色 + 可点来源 |
| ⑥ 持续追踪 | 按 6h / 24h / 周比较证据与判定指纹 | 仅实质变化时推送通知 |

#### 可信来源白名单（v0.5.2 起）

证据池采用严格白名单（`app/verification/source_policy.py`），只允许四类来源：

| 类别 | 范围 | 理由 |
| --- | --- | --- |
| Top30 公信力媒体 | Reuters / AP / AFP / BBC 等 30 家及其权威变体域名 | 交叉核查的基准来源 |
| 专业事实核查机构 | Snopes、FactCheck.org、PolitiFact、Full Fact、AFP Fact Check、Lead Stories 等 | 专门审核公开事实声明 |
| 全球搜索引擎入口 | Google、Bing、DuckDuckGo、Yahoo、Brave、Startpage | 仅作为可追溯的检索入口，不充当编辑证据 |
| 权威一手资料机构 | NASA、NOAA、WHO、UN、OECD、Science、PNAS 等 | 可直接核对的原始资料 |

百度百科/文库、QQ、搜狐、虎嗅、维基百科等聚合站、百科站与内容农场在检索阶段即被拒绝，不进入证据池，也不会出现在前端「来源」链接中。白名单通过 `/api/source-policy` 与页面「可信来源白名单」面板公开，便于审计。

每一步都会写入 `jobs.result.progress`，前端把它渲染成实时时间线。

### 3.2 允许的结论

判定器必须且只能选择以下之一：

- `supported`：有充分支持证据；
- `refuted`：有充分反驳证据；
- `mixed`：支持与反驳并存；
- `insufficient_evidence`：未找到可靠证据（默认兜底）；
- `outdated`：过去为真，现已变化；
- `not_checkable`：主观评价、未来预测等无法核查。

### 3.3 防止过度断言的规则

- 指控不等于事实，调查不等于定罪。
- 没有证据不等于“假”。
- 页面抓取失败标记为抓取失败，不计为“没有证据”。
- 没有可打开来源 URL 的判定会被拒绝或降级为 `insufficient_evidence`。
- 同一通稿的转载只算一条独立性链。
- 政治与快速变化事件保留时间边界和不确定性。
- 所有外部 URL 在访问前做 SSRF 校验。

**最终结论形态**：每条主张给出一个受约束标签 + 置信度 + 理由 + 反证 + 证据缺口 + 引用 URL；每个事件给出总结、30 家媒体覆盖图和追踪状态。系统报告的是“检索时刻证据支持到什么程度”，不宣称永久真理。

---

## 4. 所有数据源的依据、来源与组合方式

### 4.1 输入通道

| 通道 | 入口 | 说明 |
| --- | --- | --- |
| 网页控制台 | `POST /submit` 或 `POST /api/v1/check` | 文本框 + 模式（full / top30 / method）+ 追踪频率 |
| Telegram Bot | `/check`、`/deep`、`/track`、`/status`、`/history` | aiogram 长轮询；token 失效时优雅降级 |
| Public API v1 | API Key 请求头 | 供 Agent 与自动化系统调用 |

### 4.2 检索与抽取

- `unified_search()` 按配置选择搜索提供方：保留历史函数名的 `ddgs`、Brave Search 或 SearXNG。
- 在 NAS 网络里，`search_duckduckgo()` 显式优先锁定 `yahoo` 后端，失败再退 `duckduckgo`；避免 ddgs 轮询 7 个后端，Top30 阶段从约 146 秒降到约 44 秒。
- 配置密钥时，Google Fact Check 结果作为官方核查材料置前，然后按 URL 去重。
- `fetch_url()` 校验 URL、拦截私网目标并计算内容哈希。
- `extract_text()` 用 trafilatura 类抽取获得正文；送入判定器的片段有长度上限。

### 4.3 来源模型与独立性

每条证据保存 `url`、`domain`、`content_hash`、`independence_chain_id`、`snippet_hash`、抓取状态和可选发布时间。独立性链 ID 由域名 + 正文前 80 个归一化字符的 SHA-256 前缀组成。相同链条被折叠，因此通稿瀑布不会被误当成许多独立证人。

### 4.4 Top30 媒体榜依据

`app/verification/top_media.py` 按“事实准确性 + 编辑独立性”定义 30 家媒体：

1. 全球通讯社与公共广播：Reuters、AP、AFP、BBC、NPR、PBS、DW、France 24、NHK World、ABC AU；
2. 国际/全国报纸与财经媒体：NYT、Washington Post、Guardian、FT、WSJ、Economist、Time、Newsweek、CNN、Al Jazeera；
3. 专业事实核查、学术与区域权威：Snopes、FactCheck.org、Politifact、Full Fact、The Conversation、Scientific American、Nature News、The Canadian Press、The Hindu、Sydney Morning Herald。

`check_top_media()` 先做少量宽搜索，把结果按域名匹配到榜单（处理 `www.` 与 `bbc.co.uk` 等别名），再对少量重要未命中媒体补 `site:` 查询。前端在 `hit_count > 0` 时点亮绿灯，否则灰色，并展示每一条来源链接。

### 4.5 组合顺序

```
用户输入
  -> Event + queued Job
  -> claims[]
  -> （原句搜索 + 反证搜索）-> sources[] -> 独立性去重
  -> verdicts[]（六标签受约束 LLM 输出）
  -> Top30 覆盖图（域名匹配 + site: 补充）
  -> job.result { summary, progress, top_media, media_hits, total_reports }
  -> Telegram 推送 + 网页渲染
  -> Subscription 轮询 -> 指纹差异 -> Notification
```

LLM 通过 OpenAI 兼容客户端访问主备端点（`LLM_BASE_URL`、`LLM_BASE_URL_FALLBACK`）。关闭客户端内部重试，由 `app/verification/llm.py` 做端点切换和小型熔断，避免长时间重试风暴。

### 4.6 持久化

PostgreSQL 表：`events`、`claims`、`sources`、`evidence`、`verdicts`、`jobs`、`subscriptions`、`notifications`。子表使用 `ON DELETE CASCADE`。任务结果用 JSON 字段保存，使流水线演进灵活，同时核心关系表保持可审计。

---

## 5. 最终的实验结果

以下结果来自群晖 N150-P NAS 上的本地部署，不是合成基准测试。

| 检查项 | 结果 |
| --- | --- |
| `/health` | HTTP 200 |
| 前端 JavaScript 语法 | `node --check` 通过；v0.5.1 后渲染脚本约 2.77 万字符 |
| `/api/top-media` | 返回 30 家，含排名、事实等级、独立性、类型与 URL |
| 端到端完整核查 | 样本任务约 101 秒完成，状态 `done` |
| 媒体交叉核查 | 30 家中 10 家点亮，20 条可打开的相关来源 |
| 局域网与公网 | `http://192.168.8.253:8095` 与 `https://new.caishen.today` 均更新为新构建 |
| API 主备切换 | 主备端点均为 HTTP 200；强制主失败后成功切到备用 |
| 搜索优化 | 优先 yahoo 后端，Top30 阶段本地从约 146 秒降到约 44 秒 |
| 历史清理 | 备份后删除 15 个 failed 任务与 1 个孤立测试事件，剩余 8 个全部成功 |
| 多风格界面 | 4 套模板实时切换，选择本地持久化，版本弹窗展示更新历史 |

解读：在本地 NAS 上，流水线约两分钟内给出稳定、可检查的结果。主要耗时是媒体交叉核查，因此采用“宽搜索域名匹配优先、定点 `site:` 补充”的策略。系统面向个人与小团队使用，不构成法律或专业裁决权威。

---

## 6. 如何使用

### 6.1 网页控制台

1. 打开局域网或公网地址，输入 PIN 登录。
2. 可在顶部选择风格模板（极光 / 纸张 / 石墨 / 终端）。
3. 粘贴文本或链接，选择模式与追踪频率，然后提交。
4. 任务会立即出现在历史顶部；运行中详情弹窗每 3 秒刷新。
5. 点击任务查看判定、证据、进度时间线和 30 家媒体覆盖图。
6. 用「📡 追踪状态」查看所有更新，用「⚙️ 设置」修改频率、下次时间与暂停状态。
7. 底部系统面板显示 CPU、内存、磁盘与外部 API 实时状态。

### 6.2 Telegram

`/help`、`/check <文本>`、`/deep <文本>`、`/track <事件ID> [6h|24h|week]`、`/untrack`、`/status`、`/history`、`/privacy`。

### 6.3 Public API v1

```bash
curl -H "X-API-Key: $API_KEY" https://new.caishen.today/api/v1/version
curl -H "X-API-Key: $API_KEY" -H 'Content-Type: application/json' \
  -d '{"text":"...","mode":"full","freq":"none"}' \
  https://new.caishen.today/api/v1/check
```

---

## 7. 版本与发布流程

`app/version.py` 是版本号和更新记录的唯一编写处。网页徽标、登录页、`/api/version`、`/api/v1/status`、`pyproject.toml`、`compose.yaml`、README 与 CHANGELOG 均从它派生或与之对齐。

每次发布：

1. 更新 `app/version.py` 的 `VERSION`、`RELEASE_DATE`、`CODENAME` 与 `RELEASES`；
2. 同步 `pyproject.toml`、`compose.yaml`、`CHANGELOG.md`；
3. 更新英文、中文、日文说明文档；
4. 运行 `./scripts/sync_github.sh` 提交并推送脱敏源码；
5. 部署到 NAS，验证 `/health`、`/api/version` 与页面版本徽标。

---

## 7.5 v0.6.0 新增能力

- **多风格与背景音乐**：9 套可切换主题（极光/纸张/石墨/终端/海洋/森林/日落/紫罗兰/素黑白），选择本地持久化；背景音乐为 Web Audio 生成式氛围音（细雨/海浪/森林/夜曲），可开关、切换、调音量，无需外部音频文件。
- **来源可读性与可视化**：Top30 面板常驻滚动条；每条证据标题右侧方括号显示媒体名、全球可信榜名次、事实等级与报道时间。
- **合规信息采集增强**（`app/ingest/open_web.py`）：以公开 RSS / Google News RSS 扩大候选发现，遵守 robots.txt、按域名限速、有限重试；不绕过登录/付费墙/验证码；所有候选仍经可信来源白名单过滤后才进入证据池。
- **多即时通讯接入**（`app/integrations/`）：参考 NoneBot/OneBot、Kirara AI 等成熟多通道框架的「适配器 + 配置驱动 + 统一入口」思路，提供 Telegram 及 Discord/Slack/飞书/钉钉/企业微信/公众号/QQ(OneBot)/LINE/Matrix/通用 Webhook 的接入抽象；统一入口为 `POST /api/v1/im/{key}/webhook`。
- **后台管理** `/admin`（PIN `1314`）：查看（脱敏）API 配置、查看接入通道状态、发送测试回执；修改 `.env` 后需重启容器生效。
- **理论来源专题页** `/theory`：公开页面，包含方法论、可信度频段体系由来、SVG 体系图、逐条引用出处、学术与全球评价。

## 7.6 v0.6.1 新增：背景声景库

- **20 种生成式声景**（原为 4 首）：白噪音、颂钵、佛教庭院、室外鸟叫、细雨、雷雨、溪流、风铃、夏夜虫鸣、篝火、寺院钟声、月光、竹林、雪落等。每个曲目由一层或多层 `noise` / `pad` / `chirp` / `strike` 音源组成，全部用 Web Audio 实时合成，无需外部音频文件，也不产生网络请求。
- **交互**：点击某个声音立即播放；再点同一个声音停止；点击其他声音自动切换。曲目列表可滚动，20 种声音全部可达；面板底部保留播放/停止按钮。
- **自动淡出**：面板在 5 秒无操作后淡出，也可点 × 手动关闭；点击、移动鼠标、拖动音量或滚动都会重新计时。淡出只收起面板，不中断播放。
- **音量**：滑块使用 `oninput`，拖动过程中实时生效并显示百分比；曲目与音量保存在 `localStorage`（`nv_music_track`、`nv_music_vol`）。
- **验证**：发布前执行渲染后脚本语法校验（`ast` + `node --check`）与交互行为模拟测试（播放/停止/切换/音量）。

## 7.7 v0.7.0 新增：交互式即时通讯接入向导

- **设计来源**：参考 AstrBot、NoneBot、Koishi 等成熟多平台机器人框架的「适配器 + 配置驱动 + WebUI 向导」模式，但**不引入其运行时**（避免 NAS 依赖膨胀、架构重写），只在现有 `app/integrations/` 之上补齐交互式配置体验。
- **接入向导** `/admin/im`：11 个主流平台（Telegram、Discord、Slack、飞书、钉钉、企业微信、微信公众号、QQ/OneBot、LINE、Matrix、通用 Webhook）以卡片展示，进入后分四步：① 官方凭证获取指引（含官方配置台直达链接与逐步说明）→ ② 动态表单填写凭证 → ③ 扫码 / 接收地址复制 → ④ 真实消息测试。
- **免代码免重启**：凭证写入数据库表 `im_channel_configs`（`app/integrations/channel_store.py`），网页保存后通过 `ChannelRegistry.set_db_credentials()` 热加载即时生效；页面回显自动脱敏（`1234••••mnop`），掩码提交不覆盖真实密钥；旧的 `NV_IM_*` 环境变量保留为兼容兜底。
- **扫码绑定**：Telegram 由 `segno` 生成 `t.me/<bot>?start` 深链 SVG 二维码，用户扫码发送 `/start` 后，统一 webhook 自动记录 `bound_chat_id`，向导轮询 `/bind-status` 显示绑定完成；飞书、钉钉、企业微信、LINE、QQ/OneBot 因官方绑定流程不同，提供官方扫码入口说明与统一接收地址一键复制。
- **真实测试**：`app/integrations/__init__.py` 按各平台官方消息格式构造测试消息（飞书 `msg_type:text` + 时间戳签名、钉钉 `msgtype:text` + HMAC-SHA256 加签、企业微信、Discord `content`、Slack `text`、LINE `messages`、Matrix `m.text`、Telegram Bot API），测试结果与错误回写状态面板。
- **验证**：15 项接入逻辑测试覆盖平台引导完整性、脱敏/合并、各平台消息体与加签、未配置安全失败、二维码生成；并对渲染后 JS 执行 `node --check`。

## 7.8 v0.7.1 新增：理论页引用体系与出处核实

- **内容**：`app/web/theory.py` 由 174 行扩展为完整理论说明页，含八章：为什么需要框架、新闻真实性理论全景、理论与实现映射、方法论、频段体系来源、体系图示、学术评价、引用源注释。
- **理论全景**：按哲学层（真理符合论/融贯论/验证主义）、认知层（信源可信度、确认偏误）、方法层（FEVER/AVeriTeC/Veracity/trafilatura）、机构层（MBFC/Ad Fontes/NewsGuard/AllSides/路透研究院）四层梳理「如何看新闻真实性」的研究。
- **映射表**：逐条列出每条理论用在本系统哪一部分、如何组合，明确「理论 → 形态 → 防偏差 → 流程 → 排序」的链路。
- **引用注释**：正文 `[1]`–`[17]` 编号引用跳转文末；每条给出原文地址（arXiv / ACL Anthology / DOI / 官方页，多来源全列）、最早发表机构、年份、理论依据与系统用途。共 27 个不同的原文外链。
- **出处核实**：修正旧页错误引用——FEVER 应为 arXiv:1803.05355（NAACL 2018）、AVeriTeC 为 arXiv:2305.13117（NeurIPS 2023）、trafilatura 为 ACL 2021.acl-demo.15；补充 Hovland & Weiss 1951（DOI 10.1086/266350，耶鲁）、Nickerson 1998（DOI 10.1037/1089-2680.2.2.175，Tufts）、斯坦福哲学百科 Truth 条目等奠基来源。
- **验证**：`py_compile` 通过；正文引用编号与文末注释编号完全一致（1–17）；HTML 标签闭合检查全部通过；27 条原文链接无重复错误号。

### 7.9 v0.7.2 新增：交互式追踪脑图与全面 bug 修复

- **追踪脑图**（`showMindmap` / `showEventMindmap`，实现于 `app/web/app.py`）：针对“每条新闻的完整性如何更直观呈现”的需求，提供两种视图。
  - **全景视图**：不传事件 ID，一屏以卡片展示所有新闻任务的状态、结论、主张数、媒体覆盖与追踪标记，点击卡片进入单条脑图。
  - **单条脑图**：以该新闻为根节点，向四周展开六个可折叠分支——①主张与判定（逐条主张 + 标签 + 置信度）②证据与溯源（去重来源、可点开原文、媒体名次）③媒体覆盖（Top30 点亮数与媒体名）④持续追踪（活跃状态、下次检查、可读更新记录）⑤处理进度（时间线）⑥任务历史（执行次数与时间）。
  - **交互**：每个节点点击展开/收起（`mmToggle`），支持全部展开/收起（`mmExpandAll`），根节点与工具栏可直达事件详情；视图标记 `_modalView` 确保切换视图后轮询不覆盖当前内容。
  - **风格**：纯 CSS 变量实现（点阵画布、渐变根节点、状态色边框），自动适配全部 9 套主题，无外部依赖。
- **可读追踪更新**：`Notification.kind` 现写入“证据变化 · N 家来源”/“追踪已启动 · 建立基线”等摘要，前端据此显示，不再只有 64 位哈希。
- **bug 修复清单**：见 CHANGELOG v0.7.2，涵盖 freq 订阅落实、progress 合并保留、列表追踪节点状态、轮询清理、追踪通知多渠道广播、Top30 判空、recheck 原文、v1 track 去重、弹窗转义。

---

## 8. 局限

- 评级是参考而非授权，媒体顺序是咨询性排序。
- 搜索引擎可能限流，很新或未被索引的事件覆盖可能不完整。
- LLM 判定是概率性的，必须与证据和缺口一起阅读。
- PIN 保护的是个人控制台；若开放给多人，应增加 HTTPS、按用户鉴权与限流。
- 结果是某一时刻的快照。持续追踪正是为了应对事实会变化。
