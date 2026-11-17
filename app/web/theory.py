"""「理性查看新闻理论来源」专题页面。

一份可公开访问的、自包含的理论说明页面：方法论、可信度「频段」体系
的由来、体系图示、逐条引用出处、学术界与全球评价。所有内容以公开学术
与机构来源为依据，明确区分「参考性框架」与「官方认证数据」。
"""

from __future__ import annotations

# 主题配色（跟随主站语义变量名的简化版，页面自身可独立渲染）
PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>理性查看新闻理论来源 · NewsVerify</title>
<style>
:root{color-scheme:dark;--bg:#08101f;--bg2:#0d1628;--card:#111c33;--card2:#162240;--border:#1e2d4d;
--text:#e6edf7;--muted:#8b9bb5;--accent:#38bdf8;--accent2:#818cf8;--accent3:#34d399;--warn:#f59e0b;--shadow:0 12px 34px rgba(0,0,0,.35)}
body{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:radial-gradient(1100px 520px at 12% -8%,#1a2a4a 0%,transparent 60%),radial-gradient(900px 460px at 90% 0%,#1f1a3a 0%,transparent 60%),var(--bg);color:var(--text);margin:0;line-height:1.75}
.wrap{max-width:1000px;margin:0 auto;padding:32px 20px 64px}
header h1{font-size:28px;margin:0 0 6px;color:var(--accent)}
.kicker{font-size:11px;letter-spacing:2px;color:var(--accent2);font-weight:800;margin-bottom:8px}
.sub{color:var(--muted);font-size:13px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 28px;padding:10px;border:1px solid var(--border);border-radius:14px;background:var(--card)}
.nav a{font-size:12px;padding:6px 11px;border-radius:8px;color:var(--muted)}
.nav a:hover{background:var(--card2);color:var(--accent)}
section{background:linear-gradient(180deg,var(--card),var(--card2));border:1px solid var(--border);border-radius:16px;padding:22px;margin-bottom:18px;box-shadow:var(--shadow)}
h2{font-size:19px;color:var(--accent);margin:0 0 12px}h3{font-size:15px;color:var(--accent2);margin:18px 0 6px}
p,li{font-size:14px;color:var(--text)}p{margin:8px 0}ul,ol{margin:8px 0 8px 22px}li{margin:5px 0;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0}th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--accent);font-size:12px}td{color:var(--muted)}
.tag{display:inline-block;font-size:10px;padding:2px 8px;border-radius:999px;background:rgba(56,189,248,.12);color:var(--accent);border:1px solid rgba(56,189,248,.3)}
.ref{font-size:12px;color:var(--muted)}.ref b{color:var(--accent3)}
.callout{border-left:3px solid var(--warn);background:rgba(245,158,11,.07);padding:10px 14px;border-radius:0 8px 8px 0;font-size:13px;color:var(--muted);margin:12px 0}
svg{width:100%;height:auto;background:var(--bg2);border:1px solid var(--border);border-radius:12px;margin:10px 0}
.footer{text-align:center;color:var(--muted);font-size:11px;margin-top:28px}
</style></head><body><div class="wrap">
<header>
  <div class="kicker">NEWSVERIFY · THEORETICAL FOUNDATIONS</div>
  <h1>理性查看新闻理论来源</h1>
  <div class="sub">本页整理 NewsVerify 采用的方法论、可信度「频段」体系的来源与由来、体系图示、逐条引用出处，以及其在学术界与全球评价中的位置。<a href="/">← 返回控制台</a></div>
</header>

<div class="nav">
  <a href="#why">为什么需要理论框架</a>
  <a href="#method">用到的方法论</a>
  <a href="#bands">频段体系与由来</a>
  <a href="#diagram">体系图示</a>
  <a href="#sources">引用出处</a>
  <a href="#academia">学术与全球评价</a>
</div>

<section id="why">
  <h2>一、为什么需要一套理论框架</h2>
  <p>single 新闻真假不是「感觉」，而是可以被拆解、被检索、被交叉验证的证据问题。事实核查研究（fact-checking / claim verification）近十年形成了可复用的方法论：把断言拆成原子主张、为每条主张寻找支持与反驳证据、判断证据来源是否独立、保留不确定性而不是强行给出真伪。</p>
  <p>NewsVerify 把这些学术方法工程化，并额外强调两点：<b>来源透明度</b>（每条结论都能点开原文）与<b>可信度分层</b>（不是所有来源等权）。本页说明这些做法的理论出处。</p>
  <div class="callout">重要声明：系统中的「全球可信媒体 Top 30」与「可信度频段」是<b>参考性框架</b>，综合公开研究整理，用于交叉验证时的优先排序；它不是任何机构官方认证的名次，也不代表对单篇报道真伪的判定。</div>
</section>

<section id="method">
  <h2>二、用到的方法论</h2>
  <table>
    <tr><th>方法论</th><th>系统里的用法</th><th>学术/机构出处</th></tr>
    <tr><td>主张分解（Claim Decomposition）</td><td>把新闻拆成可独立验证的原子主张</td><td>FEVER：Fact Verification and Evidence Retrieval（ACL 2018）</td></tr>
    <tr><td>证据优先核查（Evidence-first）</td><td>先检索证据，再让 LLM 只基于证据判定，并输出缺口</td><td>AVeriTeC：Real-World Claim Verification（arXiv:2406.19263 / 2025 评测）</td></tr>
    <tr><td>来源独立性（Source Independence）</td><td>转载链折叠为同一独立性链，避免「多家转载=多份证据」</td><td>Veracity 等开源核查实践；新闻来源独立性研究</td></tr>
    <tr><td>事实核查分级标签</td><td>supported / refuted / mixed / insufficient 等受约束标签</td><td>FactCheck.org、PolitiFact、Full Fact 的公开评级方法</td></tr>
    <tr><td>可信度频段</td><td>按「事实报道质量 + 编辑独立性」对来源分层</td><td>MBFC、NewsGuard、Ad Fontes Media Bias Chart、AllSides</td></tr>
    <tr><td>公众信任度研究</td><td>作为媒体排序的背景依据</td><td>Reuters Institute《Digital News Report》</td></tr>
  </table>
</section>

<section id="bands">
  <h2>三、为什么用「频段体系」，它从哪里来</h2>
  <p>「频段」指的是把媒体按可信度/偏见连续区间分层，而不是简单分成「真/假」两类。这套做法来自多家公开评级机构的成熟实践：</p>
  <ul>
    <li><b>Media Bias/Fact Check（MBFC）</b>：用 Very High / High / Mostly Factual 等事实报道分级，并单列政治偏见。NewsVerify 的 <code>factual</code> 字段参考此口径。</li>
    <li><b>Ad Fontes Media Bias Chart</b>：把媒体放在「偏见（横轴）× 可靠性（纵轴）」二维图上，形如「频段」。</li>
    <li><b>NewsGuard</b>：按九条新闻可信标准给出 0–100 分与红/绿评级。</li>
    <li><b>AllSides</b>：以左右偏见频谱标注媒体与新闻。</li>
    <li><b>Reuters Institute 数字新闻报告</b>：提供跨国家公众媒体信任度数据。</li>
  </ul>
  <p>NewsVerify 不购买或转售这些机构的授权数据，也不伪造它们的分数；只把<b>公开方法论</b>作为排序思路，并在未获授权处标注 <span class="tag">not_connected</span> / <span class="tag">context_only</span>。</p>
</section>

<section id="diagram">
  <h2>四、整套体系图示（来源讲解）</h2>
  <svg viewBox="0 0 960 470" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="NewsVerify 理论与数据体系图">
    <defs>
      <linearGradient id="gg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#818cf8"/></linearGradient>
      <marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#38bdf8"/></marker>
    </defs>
    <!-- Column headers -->
    <text x="120" y="30" text-anchor="middle" fill="#38bdf8" font-size="14" font-weight="800">① 理论来源</text>
    <text x="470" y="30" text-anchor="middle" fill="#818cf8" font-size="14" font-weight="800">② 方法论流水线</text>
    <text x="830" y="30" text-anchor="middle" fill="#34d399" font-size="14" font-weight="800">③ 输出与评价</text>
    <!-- theory nodes -->
    <g font-size="11" fill="#e6edf7">
      <rect x="20" y="50" width="200" height="42" rx="9" fill="#111c33" stroke="#38bdf8"/><text x="120" y="68" text-anchor="middle">FEVER（ACL 2018）</text><text x="120" y="83" text-anchor="middle" fill="#8b9bb5">主张分解 · 证据检索</text>
      <rect x="20" y="104" width="200" height="42" rx="9" fill="#111c33" stroke="#38bdf8"/><text x="120" y="122" text-anchor="middle">AVeriTeC（2024/25）</text><text x="120" y="137" text-anchor="middle" fill="#8b9bb5">证据优先 · 保留缺口</text>
      <rect x="20" y="158" width="200" height="42" rx="9" fill="#111c33" stroke="#818cf8"/><text x="120" y="176" text-anchor="middle">MBFC / NewsGuard</text><text x="120" y="191" text-anchor="middle" fill="#8b9bb5">事实分级 · 可信评分</text>
      <rect x="20" y="212" width="200" height="42" rx="9" fill="#111c33" stroke="#818cf8"/><text x="120" y="230" text-anchor="middle">Ad Fontes / AllSides</text><text x="120" y="245" text-anchor="middle" fill="#8b9bb5">偏见×可靠性频段</text>
      <rect x="20" y="266" width="200" height="42" rx="9" fill="#111c33" stroke="#818cf8"/><text x="120" y="284" text-anchor="middle">Reuters Institute</text><text x="120" y="299" text-anchor="middle" fill="#8b9bb5">公众信任度研究</text>
      <rect x="20" y="320" width="200" height="42" rx="9" fill="#111c33" stroke="#34d399"/><text x="120" y="338" text-anchor="middle">Veracity / trafilatura</text><text x="120" y="353" text-anchor="middle" fill="#8b9bb5">独立性 · 正文抽取</text>
    </g>
    <!-- pipeline nodes -->
    <g font-size="11" fill="#e6edf7">
      <rect x="360" y="60" width="220" height="40" rx="9" fill="url(#gg)"/><text x="470" y="85" text-anchor="middle" fill="#08101f" font-weight="800">① 拆成原子主张</text>
      <rect x="360" y="120" width="220" height="40" rx="9" fill="url(#gg)"/><text x="470" y="145" text-anchor="middle" fill="#08101f" font-weight="800">② 多源检索 + RSS 公开源</text>
      <rect x="360" y="180" width="220" height="40" rx="9" fill="url(#gg)"/><text x="470" y="205" text-anchor="middle" fill="#08101f" font-weight="800">③ 来源白名单 + 独立性判定</text>
      <rect x="360" y="240" width="220" height="40" rx="9" fill="url(#gg)"/><text x="470" y="265" text-anchor="middle" fill="#08101f" font-weight="800">④ LLM 受约束判定（六标签）</text>
      <rect x="360" y="300" width="220" height="40" rx="9" fill="url(#gg)"/><text x="470" y="325" text-anchor="middle" fill="#08101f" font-weight="800">⑤ Top30 交叉核查 + 点亮</text>
      <rect x="360" y="360" width="220" height="40" rx="9" fill="url(#gg)"/><text x="470" y="385" text-anchor="middle" fill="#08101f" font-weight="800">⑥ 持续追踪 + 实质变化通知</text>
    </g>
    <!-- output nodes -->
    <g font-size="11" fill="#e6edf7">
      <rect x="720" y="90" width="220" height="46" rx="9" fill="#0a1a16" stroke="#34d399"/><text x="830" y="110" text-anchor="middle">带出处的判定结论</text><text x="830" y="126" text-anchor="middle" fill="#8b9bb5">标签/置信度/反证/缺口/URL</text>
      <rect x="720" y="170" width="220" height="46" rx="9" fill="#0a1a16" stroke="#34d399"/><text x="830" y="190" text-anchor="middle">可信度频段排序</text><text x="830" y="206" text-anchor="middle" fill="#8b9bb5">Top30 媒体 + 事实等级</text>
      <rect x="720" y="250" width="220" height="46" rx="9" fill="#0a1a16" stroke="#34d399"/><text x="830" y="270" text-anchor="middle">可审计的白名单</text><text x="830" y="286" text-anchor="middle" fill="#8b9bb5">允许类别 + 明确拒绝</text>
      <rect x="720" y="330" width="220" height="70" rx="9" fill="#1f1a3a" stroke="#f59e0b"/><text x="830" y="352" text-anchor="middle">学术界与全球评价</text><text x="830" y="370" text-anchor="middle" fill="#8b9bb5">FEVER/AVeriTeC 评测</text><text x="830" y="386" text-anchor="middle" fill="#8b9bb5">DNR 信任度 · 研究引用</text>
    </g>
    <!-- arrows theory -> pipeline -->
    <g stroke="#38bdf8" stroke-width="1.4" marker-end="url(#ar)" fill="none">
      <path d="M220,71 C300,71 300,80 360,80"/>
      <path d="M220,125 C300,125 300,140 360,140"/>
      <path d="M220,179 C300,179 300,200 360,200"/>
      <path d="M220,233 C300,233 300,260 360,260"/>
      <path d="M220,287 C300,287 300,320 360,320"/>
      <path d="M220,341 C300,341 300,380 360,380"/>
    </g>
    <g stroke="#34d399" stroke-width="1.4" marker-end="url(#ar)" fill="none">
      <path d="M580,80 C660,80 660,113 720,113"/>
      <path d="M580,200 C660,200 660,193 720,193"/>
      <path d="M580,260 C660,260 660,273 720,273"/>
      <path d="M580,380 C660,380 660,365 720,365"/>
    </g>
    <text x="470" y="440" text-anchor="middle" fill="#8b9bb5" font-size="11">左侧为公开学术与机构来源 → 中部为可复现的核查流水线 → 右侧为带出处、可审计的输出及其学术评价</text>
  </svg>
</section>

<section id="sources">
  <h2>五、引用出处（逐条来源）</h2>
  <table>
    <tr><th>来源</th><th>类型</th><th>具体出处</th></tr>
    <tr><td>FEVER</td><td>学术论文</td><td class="ref"><b>Nie et al., "Fever: A Large-scale Dataset for Fact Extraction and VERification", NAACL 2018.</b> arXiv:1803.01155</td></tr>
    <tr><td>AVeriTeC</td><td>学术论文/评测</td><td class="ref"><b>"AVeriTeC: Real-World Claim Verification with Evidence from the Web", 2024/2025.</b> arXiv:2406.19263</td></tr>
    <tr><td>Media Bias/Fact Check</td><td>评级机构（公开方法）</td><td class="ref"><b>mediabiasfactcheck.com</b> — 事实报道分级与偏见方法说明</td></tr>
    <tr><td>Reuters Institute</td><td>学术研究</td><td class="ref"><b>Digital News Report</b>（牛津大学路透新闻研究院年度调查）</td></tr>
    <tr><td>NewsGuard</td><td>评级机构</td><td class="ref"><b>newsguardtech.com</b> — 九条可信度标准</td></tr>
    <tr><td>Ad Fontes Media</td><td>评级机构</td><td class="ref"><b>adfontesmedia.com</b> — Media Bias Chart 方法</td></tr>
    <tr><td>AllSides</td><td>评级机构</td><td class="ref"><b>allsides.com</b> — 偏见频谱方法</td></tr>
    <tr><td>FactCheck.org / PolitiFact / Full Fact</td><td>事实核查机构</td><td class="ref">各机构公开评级标准与文章（factcheck.org / politifact.com / fullfact.org）</td></tr>
    <tr><td>Google Fact Check Tools</td><td>公开 API</td><td class="ref"><b>factchecktools.googleapis.com</b> — 专业核查机构的 textualRating</td></tr>
    <tr><td>trafilatura</td><td>开源软件/论文</td><td class="ref"><b>Barbaresi, "Trafilatura: A Web Scraping Library...", ACL/IJCNLP 2021 System Demonstrations.</b></td></tr>
    <tr><td>Veracity</td><td>学术论文</td><td class="ref"><b>arXiv:2506.15794</b> — 来源透明度与独立性实践</td></tr>
    <tr><td>Wikipedia / Britannica</td><td>百科背景</td><td class="ref">仅作概念背景参考，<b>不作为系统证据来源</b>（见可信来源白名单）</td></tr>
  </table>
</section>

<section id="academia">
  <h2>六、在学术界与全球评价中的位置</h2>
  <h3>学术脉络</h3>
  <p>自动事实核查是 NLP 与新闻学的交叉领域。FEVER 确立了「检索—验证」范式，AVeriTeC 把任务推进到真实网页证据与不确定性表达，NewsVerify 的工程流水线正是这些范式的落地：不追求「一句话定罪」，而是输出可追溯的证据链与保留缺口。</p>
  <h3>全球评价与局限</h3>
  <ul>
    <li>Reuters Institute《Digital News Report》持续跟踪多国公众对媒体的信任差异，说明「信任」因国家与群体而异——因此系统把信任度作为背景而非绝对评分。</li>
    <li>MBFC / NewsGuard / Ad Fontes 等评级体系方法不同、口径不同，业界并无单一权威排名；系统的 Top30 是综合参考，明确标注「非官方名次」。</li>
    <li>LLM 判定具概率性，学界普遍强调应把结论与证据、缺口并读；系统据此强制输出反证与证据缺口，避免误导。</li>
  </ul>
  <div class="callout">本页所有外部链接指向各机构/论文的公开页面；系统不使用任何未经授权的商业评级数据，不伪造评分，也不把百科站纳入证据池。</div>
</section>

<div class="footer">NewsVerify · 理性查看新闻理论来源 · 本页为公开说明，随版本更新</div>
</div></body></html>"""
