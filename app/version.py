"""Single source of truth for product version and release notes.

Every user-visible surface (Web UI, API, docs, deployment scripts) should read
from this module instead of hard-coding a version string.
"""

from __future__ import annotations

VERSION = "0.5.2"
RELEASE_DATE = "2026-11-17"
CODENAME = "Verity"

THEMES = [
    {"key": "aurora", "name": "极光 · Aurora", "description": "深蓝玻璃质感，默认风格"},
    {"key": "paper", "name": "纸张 · Paper", "description": "浅色阅读友好风格"},
    {"key": "slate", "name": "石墨 · Slate", "description": "中性专业的控制台风格"},
    {"key": "terminal", "name": "终端 · Terminal", "description": "高对比等宽终端风格"},
]

RELEASES = [
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
