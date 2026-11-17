"""Single source of truth for product version and release notes.

Every user-visible surface (Web UI, API, docs, deployment scripts) should read
from this module instead of hard-coding a version string.
"""

from __future__ import annotations

VERSION = "0.7.0"
RELEASE_DATE = "2026-11-17"
CODENAME = "Bridge"

THEMES = [
    {"key": "aurora", "name": "极光 · Aurora", "description": "深蓝玻璃质感，默认风格"},
    {"key": "paper", "name": "纸张 · Paper", "description": "浅色阅读友好风格"},
    {"key": "slate", "name": "石墨 · Slate", "description": "中性专业的控制台风格"},
    {"key": "terminal", "name": "终端 · Terminal", "description": "高对比等宽终端风格"},
    {"key": "ocean", "name": "海洋 · Ocean", "description": "深海青蓝，沉静通透"},
    {"key": "forest", "name": "森林 · Forest", "description": "自然墨绿，护眼舒缓"},
    {"key": "sunset", "name": "日落 · Sunset", "description": "暖橙玫红，温暖柔和"},
    {"key": "violet", "name": "紫罗兰 · Violet", "description": "深紫优雅，专注沉浸"},
    {"key": "mono", "name": "素黑白 · Mono", "description": "黑白衬线，纸质阅读"},
]

RELEASES = [
    {
        "version": "0.7.0",
        "date": "2026-11-17",
        "codename": "Bridge",
        "summary": "主流即时通讯接入改为交互式向导：扫码/Token 辅助、填表即生效、一键真实测试，无需改代码或重启",
        "changes": [
            "新增独立接入向导页 /admin/im：11 个主流平台卡片式引导，四步完成接入（官方凭证 → 填表 → 扫码/回调 → 测试）",
            "新增数据库凭证存储 im_channel_configs：网页保存后立即生效并跨重启保留，页面回显自动脱敏，彻底告别改 .env 代码与重启容器",
            "每个平台提供官方配置台直达链接、逐步操作说明与所需字段说明，全部来自平台官方文档",
            "扫码绑定：Telegram 生成 t.me 深链二维码并轮询 /start 完成绑定；飞书/钉钉/企业微信/LINE/QQ OneBot 提供官方扫码入口与接收 URL 复制",
            "统一接收地址一键复制，按平台给出填入位置提示；支持飞书/钉钉加签、Slack 签名密钥等安全校验",
            "一键真实测试：按各平台官方消息格式构造测试消息（飞书/钉钉/企微/Discord/Slack/LINE/Matrix/Telegram），结果回写状态",
            "新增 segno 二维码依赖与渠道凭证脱敏/合并逻辑，附 15 项接入逻辑自动测试",
        ],
    },
    {
        "version": "0.6.1",
        "date": "2026-11-17",
        "codename": "Echo",
        "summary": "背景音乐扩展为 20 种声景，点击即播放、再点即停止，面板 5 秒无操作自动淡出",
        "changes": [
            "背景音乐从 4 首扩展到 20 种 Web Audio 生成式声景：白噪音、颂钵、佛教庭院、室外鸟叫、雷雨、溪流、风铃、夏夜虫鸣、篝火、寺院钟声、竹林、雪落等",
            "点击任一声音即直接播放；同一声音再点即停止；播放中点击其他声音自动切换，无需先点播放按钮",
            "音乐面板 5 秒无操作自动淡出，也可点右上角关闭；任何操作重新计时，淡出只收起面板不中断播放",
            "音量改为拖动时实时调节并显示百分比，曲目与音量偏好继续保存在本地",
            "音源引擎重构为 noise / pad / chirp / strike 分层架构，20 种声音全部实时合成，无外部音频依赖",
            "新增渲染后脚本语法校验与交互行为模拟测试，确保发布版本的播放逻辑可用",
        ],
    },
    {
        "version": "0.6.0",
        "date": "2026-11-17",
        "codename": "Prism",
        "summary": "9 套风格 + 背景音乐、合规信息采集增强、后台管理与多 IM 接入、理论来源专题页",
        "changes": [
            "页面风格从 4 套扩展到 9 套：新增海洋/森林/日落/紫罗兰/素黑白",
            "新增可开关、可切换 4 首氛围曲、可调音量的背景音乐（Web Audio 生成式，无需外部音频）",
            "30 家媒体面板加入常驻滚动条，可完整查看全部媒体",
            "证据标题右侧方括号标注媒体名、全球可信榜名次、事实等级与报道时间",
            "新增合规公开信息采集增强：RSS/Google News RSS + robots 尊重 + 限速重试，仍经可信白名单",
            "新增 /admin 后台（PIN 1314）：查看 API 配置、管理/测试主流即时通讯接入入口",
            "系统拓扑图改为统一的即时通讯工具接入（含 Telegram 在内）",
            "新增公开专题页 /theory「理性查看新闻理论来源」：方法论、频段体系由来、图示、逐条出处与学术评价",
            "证据采集跳过搜索引擎跳转/广告链接，改用对头部公信力媒体的 site: 查询补充真实报道",
        ],
    },
    {
        "version": "0.5.2",
        "date": "2026-11-17",
        "codename": "Verity",
        "summary": "严格可信来源白名单：移除百度等聚合站，证据池只收录公信力靠前的来源",
        "changes": [
            "新增 source_policy.py：白名单只含 Top30 媒体、专业事实核查机构、全球搜索引擎入口与权威一手资料机构",
            "证据检索层拦截百度百科/文库、QQ、搜狐、虎嗅、维基百科等非白名单域名，不再进入证据池",
            "Top30 媒体交叉核查的来源链接同样经过白名单过滤",
            "事件详情标注每条证据的来源类型，新增「可信来源白名单」面板与 /api/source-policy 接口",
            "新增历史数据清理脚本 scripts/clean_untrusted_sources.py（默认 dry-run）",
        ],
    },
    {
        "version": "0.5.1",
        "date": "2026-11-17",
        "codename": "Atlas",
        "summary": "修复追踪设置按钮的运行时脚本语法错误，确保页面按钮全部可用",
        "changes": [
            "修复 showTrackSettings() 中因 Python 字符串转义被吞掉而导致的整段 JS 解析失败",
            "把内嵌 onclick 改为 HTML 实体写法，避免引号嵌套歧义",
            "新增按运行时渲染结果校验前端脚本的方法，防止源码通过但页面失效",
        ],
    },
    {
        "version": "0.5.0",
        "date": "2026-11-17",
        "codename": "Atlas",
        "summary": "多风格界面模板、统一版本号、完整三语软件说明与 GitHub 同步机制",
        "changes": [
            "新增 4 套可切换页面风格：极光/纸张/石墨/终端，选择结果本地持久化",
            "新增顶部导航栏、版本徽标与「版本与更新」弹窗，界面信息层级更清晰",
            "新增统一版本模块 app/version.py，Web/API/pyproject/文档共用同一版本号",
            "新增中/英/日三语软件说明与 GitHub 同步脚本",
            "修复 NAS 运行版本落后于本地源码的问题，重新构建并验证",
        ],
    },
    {
        "version": "0.4.0",
        "date": "2026-11-17",
        "codename": "Signal",
        "summary": "Top30 媒体交叉核查、追踪设置、系统运行状况与主备 API 切换",
        "changes": [
            "Top 媒体从 10 家扩展到 30 家，按报道情况点亮/置灰并展示来源链接",
            "任务卡片新增追踪状态汇总与独立追踪设置入口",
            "新增系统运行状况面板，实时探测主备 LLM 与搜索服务",
            "LLM 客户端支持主备端点自动切换与端点级熔断",
            "修复任务列表空白、僵尸任务卡死与事件详情字段错误",
        ],
    },
]


def version_payload() -> dict:
    return {
        "version": VERSION,
        "release_date": RELEASE_DATE,
        "codename": CODENAME,
        "themes": THEMES,
        "releases": RELEASES,
    }
