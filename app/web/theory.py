"""「理性查看新闻理论来源」专题页面。

一份可公开访问的、自包含的理论说明页面。结构：
  一、为什么需要一套理论框架
  二、总体说明：如何判断一条新闻的真实性（理论全景）
  三、这些理论用在本系统的哪一部分（理论与实现映射）
  四、用到的方法论
  五、为什么用「频段体系」，它从哪里来
  六、整套体系图示
  七、在学术界与全球评价中的位置
  八、引用源注释（逐条：原文地址 / 最早发表机构 / 理论依据 / 与本系统的关系）

所有内容以公开学术与机构来源为依据；正文用 [n] 编号引用，末尾逐条给出
可点击的原文地址与出处。明确区分「参考性框架」与「官方认证数据」。
"""

from __future__ import annotations

PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>理性查看新闻理论来源 · NewsVerify</title>
<style>
:root{color-scheme:dark;--bg:#08101f;--bg2:#0d1628;--card:#111c33;--card2:#162240;--border:#1e2d4d;
--text:#e6edf7;--muted:#8b9bb5;--accent:#38bdf8;--accent2:#818cf8;--accent3:#34d399;--warn:#f59e0b;--shadow:0 12px 34px rgba(0,0,0,.35)}
body{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:radial-gradient(1100px 520px at 12% -8%,#1a2a4a 0%,transparent 60%),radial-gradient(900px 460px at 90% 0%,#1f1a3a 0%,transparent 60%),var(--bg);color:var(--text);margin:0;line-height:1.75}
.wrap{max-width:1040px;margin:0 auto;padding:32px 20px 64px}
header h1{font-size:29px;margin:0 0 6px;color:var(--accent)}
.kicker{font-size:11px;letter-spacing:2px;color:var(--accent2);font-weight:800;margin-bottom:8px}
.sub{color:var(--muted);font-size:13px}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.nav{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 28px;padding:10px;border:1px solid var(--border);border-radius:14px;background:var(--card)}
.nav a{font-size:12px;padding:6px 11px;border-radius:8px;color:var(--muted)}
.nav a:hover{background:var(--card2);color:var(--accent)}
section{background:linear-gradient(180deg,var(--card),var(--card2));border:1px solid var(--border);border-radius:16px;padding:22px;margin-bottom:18px;box-shadow:var(--shadow)}
h2{font-size:19px;color:var(--accent);margin:0 0 12px}h3{font-size:15px;color:var(--accent2);margin:20px 0 6px}
p,li{font-size:14px;color:var(--text)}p{margin:9px 0}ul,ol{margin:8px 0 8px 22px}li{margin:6px 0;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:13px;margin:10px 0}th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--accent);font-size:12px}td{color:var(--muted)}
.tag{display:inline-block;font-size:10px;padding:2px 8px;border-radius:999px;background:rgba(56,189,248,.12);color:var(--accent);border:1px solid rgba(56,189,248,.3)}
.cite{display:inline-block;font-size:10px;line-height:1;color:var(--accent3);background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.3);border-radius:5px;padding:2px 4px;margin:0 1px;vertical-align:super;text-decoration:none;font-weight:700}
.cite:hover{background:rgba(52,211,153,.25);text-decoration:none}
.layer{border-left:3px solid var(--accent2);background:rgba(129,140,248,.06);border-radius:0 10px 10px 0;padding:8px 14px;margin:12px 0}
.layer b{color:var(--accent2)}
.callout{border-left:3px solid var(--warn);background:rgba(245,158,11,.07);padding:10px 14px;border-radius:0 8px 8px 0;font-size:13px;color:var(--muted);margin:12px 0}
.reflist{list-style:none;margin:6px 0;padding:0;counter-reset:ref}
.reflist li{background:var(--bg2);border:1px solid var(--border);border-left:3px solid var(--accent3);border-radius:10px;padding:13px 15px;margin:10px 0;font-size:13px;color:var(--muted)}
.reflist li:target{border-left-color:var(--warn);background:rgba(245,158,11,.06)}
.reflist .rt{color:var(--text);font-weight:700;font-size:13.5px}
.reflist .meta{font-size:12px;color:var(--muted);margin:4px 0}
.reflist .meta b{color:var(--accent2)}
.reflist .u{font-size:11.5px;margin:3px 0;word-break:break-all}
.reflist .u a{color:var(--accent)}
.reflist .why{font-size:12px;color:var(--muted);margin-top:5px;padding-top:5px;border-top:1px dashed var(--border)}
.reflist .why b{color:var(--accent3)}
svg{width:100%;height:auto;background:var(--bg2);border:1px solid var(--border);border-radius:12px;margin:10px 0}
.footer{text-align:center;color:var(--muted);font-size:11px;margin-top:28px}
@media(max-width:720px){
  html{-webkit-text-size-adjust:100%}
  .wrap{padding:18px 12px 44px}
  header h1{font-size:22px}
  .kicker{font-size:9px;letter-spacing:1.2px}
  .sub{font-size:12px;line-height:1.7}
  .nav{flex-wrap:nowrap;overflow-x:auto;gap:5px;margin:14px -12px 20px;padding:8px 12px;
    border-radius:0;border-left:none;border-right:none;scrollbar-width:none;-webkit-overflow-scrolling:touch}
  .nav::-webkit-scrollbar{display:none}
  .nav a{flex:0 0 auto;padding:8px 11px;font-size:12px;white-space:nowrap}
  section{padding:15px 13px;border-radius:14px;margin-bottom:14px;overflow-x:auto;-webkit-overflow-scrolling:touch}
  h2{font-size:17px}h3{font-size:14px;margin:16px 0 5px}
  p,li{font-size:13px;line-height:1.75}
  ul,ol{margin-left:18px}
  table{min-width:600px;font-size:12px}
  th,td{padding:7px 8px;line-height:1.6}
  svg{min-width:720px;margin:8px 0}
  .layer,.callout{font-size:12px;padding:9px 11px}
  .reflist li{padding:11px 12px;font-size:12px}
  .reflist .rt{font-size:13px}
  .cite{font-size:9px;padding:2px 3px}
  .footer{font-size:10px;line-height:1.7}
}
</style></head><body><div class="wrap">
<header>
  <div class="kicker">NEWSVERIFY · THEORETICAL FOUNDATIONS</div>
  <h1>理性查看新闻理论来源</h1>
  <div class="sub">本页给出一套「如何判断新闻真实性」的理论全景，说明 NewsVerify 采用了其中哪些理论、如何组合落地，并逐条列出原文地址、最早发表机构与理论依据。正文中 <a class="cite" href="#r1">[n]</a> 为引用编号，可跳转到文末的引用源注释。<a href="/">← 返回控制台</a></div>
</header>

<div class="nav">
  <a href="#why">一、为什么需要框架</a>
  <a href="#overview">二、真实性理论全景</a>
  <a href="#mapping">三、理论与实现映射</a>
  <a href="#method">四、用到的方法论</a>
  <a href="#bands">五、频段体系来源</a>
  <a href="#diagram">六、体系图示</a>
  <a href="#academia">七、学术与全球评价</a>
  <a href="#sources">八、引用源注释</a>
</div>

<section id="why">
  <h2>一、为什么需要一套理论框架</h2>
  <p>新闻的真假不是「感觉」，而是一个可以被拆解、被检索、被交叉验证的证据问题。近二十年，哲学、认知科学、NLP 与新闻学各自给出了可复用的理论工具：哲学回答「什么叫真」，认知科学回答「人为何会误判」，事实核查研究回答「机器如何可复现地判断」，评级机构回答「媒体如何分层」。<a class="cite" href="#r7">[7]</a><a class="cite" href="#r5">[5]</a><a class="cite" href="#r6">[6]</a><a class="cite" href="#r1">[1]</a></p>
  <p>NewsVerify 把这些理论工程化，并额外强调两点：<b>来源透明度</b>（每条结论都能点开原文）与<b>可信度分层</b>（不是所有来源等权，依据「信源可信度」的经典实证结论）。<a class="cite" href="#r5">[5]</a></p>
  <div class="callout">重要声明：系统中的「全球可信媒体 Top 30」与「可信度频段」是<b>参考性框架</b>，综合下列公开研究整理，仅用于交叉验证时的优先排序；它不是任何机构官方认证的名次，也不代表对单篇报道真伪的判定。</div>
</section>

<section id="overview">
  <h2>二、总体说明：如何判断一条新闻的真实性（理论全景）</h2>
  <p>关于「如何看待新闻真实性」的研究，可归为四个递进的层面。它们不是互相替代，而是逐层收窄：先界定「真」，再认识「人会怎么错」，再给出「怎么核查」，最后解决「先看谁的」。</p>

  <div class="layer">
    <b>A. 哲学层 —— 「真」是什么</b>
    <p>《斯坦福哲学百科全书》"Truth" 条目系统梳理了主要真理理论：<b>符合论</b>（命题与事实对应）、<b>融贯论</b>（与可靠信念系统一致）、<b>实用/探究论</b>（Peirce、James：真理是探究的终点）、以及<b>验证主义</b>（原则上可验证）。<a class="cite" href="#r7">[7]</a></p>
    <p><b>对新闻的启示：</b>单条新闻无法「 Self-evident 地自证为真」，只能靠证据与多源一致性去逼近——这正是本系统输出「受约束标签 + 置信度 + 证据链 + 缺口」而非绝对真伪的哲学依据。</p>
  </div>

  <div class="layer">
    <b>B. 认知层 —— 人为什么会误判</b>
    <p><b>信源可信度理论</b>：Hovland 与 Weiss 1951 年在耶鲁大学的实证研究发现，同一内容由「可信」或「不可信」来源发出，受众的接受度显著不同，且存在「睡眠者效应」（时间一长，人们把内容与来源分离）。<a class="cite" href="#r5">[5]</a> 这是「来源分层」在学术上最早的实证依据之一。</p>
    <p><b>确认偏误</b>：Nickerson 1998 年综述指出，人倾向寻找、解读有利于既有信念的证据。<a class="cite" href="#r6">[6]</a> 因此核查不能依赖读者或单一模型的直觉，必须用结构化流程强制呈现反证与缺口。</p>
  </div>

  <div class="layer">
    <b>C. 方法层 —— 如何可复现地核查</b>
    <p><b>FEVER</b>（NAACL 2018）确立了「主张分解 → 证据检索 → 受约束标签（Supported / Refuted / NotEnoughInfo）」的评测范式。<a class="cite" href="#r1">[1]</a> <b>AVeriTeC</b>（NeurIPS 2023）把任务推进到真实世界声明、多步问答式证据、文本论证，并刻意规避「时间泄漏」。<a class="cite" href="#r2">[2]</a> <b>Veracity</b>（2025）强调透明、可解释、多语言与面向媒体素养的开源核查。<a class="cite" href="#r3">[3]</a> <b>trafilatura</b>（ACL 2021）解决「从网页正文抽取干净文本」这一工程前提。<a class="cite" href="#r4">[4]</a></p>
  </div>

  <div class="layer">
    <b>D. 机构层 —— 先看谁、如何给媒体分层</b>
    <p><b>MBFC</b> 用「事实报道质量 + 政治偏见」双维度分级；<a class="cite" href="#r8">[8]</a> <b>Ad Fontes Media</b> 的 Media Bias Chart® 把媒体放在「偏见（横轴）× 可靠性（纵轴）」二维坐标上；<a class="cite" href="#r10">[10]</a> <b>NewsGuard</b> 用 9 条标准给出评级；<a class="cite" href="#r9">[9]</a> <b>AllSides</b> 以左右偏见频谱标注。<a class="cite" href="#r11">[11]</a> 公众信任度层面，牛津大学路透新闻研究院《Digital News Report》持续跟踪多国差异。<a class="cite" href="#r12">[12]</a> 评级标签的方法则可参考 <b>PolitiFact</b> 的 Truth-O-Meter 六档、<a class="cite" href="#r13">[13]</a> <b>FactCheck.org</b><a class="cite" href="#r14">[14]</a> 与 <b>Full Fact</b><a class="cite" href="#r15">[15]</a> 的公开核查规范，以及 Google 的 ClaimReview 结构化标准。<a class="cite" href="#r16">[16]</a></p>
  </div>
</section>

<section id="mapping">
  <h2>三、这些理论用在本系统的哪一部分（理论与实现映射）</h2>
  <p>下表把上一节的理论逐项落到系统的具体机制，说明「用到了哪一部分、如何组合」。这是本页的核心：理论不是陈列，而是可追溯到代码与界面的设计依据。</p>
  <table>
    <tr><th>理论 / 依据</th><th>用到了哪一部分</th><th>系统里的组合方式</th><th>引用</th></tr>
    <tr><td>符合论 / 融贯论 / 验证主义</td><td>判定输出形态</td><td>不输出绝对真伪，而是「标签 + 置信度 + 证据链 + 缺口」，让结论可被读者按证据复核</td><td><a class="cite" href="#r7">[7]</a></td></tr>
    <tr><td>信源可信度理论</td><td>来源分层与白名单</td><td>证据按媒体可信度分级加权、优先取高可信来源；明确拒绝不可信域名</td><td><a class="cite" href="#r5">[5]</a></td></tr>
    <tr><td>确认偏误</td><td>反证与缺口强制输出</td><td>判定模板强制包含「反证」与「证据缺口」，对冲单向找证据的偏差</td><td><a class="cite" href="#r6">[6]</a></td></tr>
    <tr><td>FEVER 主张分解 + 受约束标签</td><td>核查流水线核心</td><td>把新闻拆成原子主张，逐条检索证据，用受约束标签输出，保留 NotEnoughInfo 类缺口</td><td><a class="cite" href="#r1">[1]</a></td></tr>
    <tr><td>AVeriTeC 真实网页证据 + 论证</td><td>证据链与时序</td><td>优先真实媒体网页证据，记录报道时间，避免用「事后证据」倒推</td><td><a class="cite" href="#r2">[2]</a></td></tr>
    <tr><td>Veracity 透明 + 可解释 + 多语言</td><td>来源透明度 / 三语文档</td><td>每条结论可点开原文；提供英文 / 中文 / 日文说明与可审计记录</td><td><a class="cite" href="#r3">[3]</a></td></tr>
    <tr><td>trafilatura 正文抽取</td><td>证据预处理</td><td>抓取后抽取正文与元数据、比对指纹，支撑独立性链折叠</td><td><a class="cite" href="#r4">[4]</a></td></tr>
    <tr><td>MBFC / Ad Fontes / NewsGuard / AllSides</td><td>可信度频段 + Top30</td><td>综合公开方法论做「事实质量 + 偏见」分层，形成 Top30 排序（标注非官方名次）</td><td><a class="cite" href="#r8">[8]</a><a class="cite" href="#r10">[10]</a><a class="cite" href="#r9">[9]</a><a class="cite" href="#r11">[11]</a></td></tr>
    <tr><td>Reuters Institute 公众信任度</td><td>排序背景</td><td>信任度作背景参考而非绝对评分，避免把单一市场的信任差异普适化</td><td><a class="cite" href="#r12">[12]</a></td></tr>
    <tr><td>PolitiFact / FactCheck.org / Full Fact / ClaimReview</td><td>标签体系与可机读引用</td><td>参考分级标签与纠错规范；结论附可点原文与来源类型，便于外部复核</td><td><a class="cite" href="#r13">[13]</a><a class="cite" href="#r14">[14]</a><a class="cite" href="#r15">[15]</a><a class="cite" href="#r16">[16]</a></td></tr>
  </table>
  <div class="callout">组合逻辑：<b>哲学层</b>决定「输出什么形态」→ <b>认知层</b>决定「必须防什么偏差」→ <b>方法层</b>提供「怎么可复现地做」→ <b>机构层</b>决定「先看谁、怎么分层」。四层共同构成从理论到界面的完整链路。</div>
</section>

<section id="method">
  <h2>四、用到的方法论</h2>
  <table>
    <tr><th>方法论</th><th>系统里的用法</th><th>学术 / 机构出处（最早发表）</th></tr>
    <tr><td>主张分解（Claim Decomposition）</td><td>把新闻拆成可独立验证的原子主张</td><td>FEVER，NAACL 2018 <a class="cite" href="#r1">[1]</a></td></tr>
    <tr><td>证据优先核查（Evidence-first）</td><td>先检索证据，再让模型只基于证据判定，并输出缺口</td><td>AVeriTeC，NeurIPS 2023 <a class="cite" href="#r2">[2]</a></td></tr>
    <tr><td>来源独立性（Source Independence）</td><td>转载链折叠为同一独立性链，避免「多家转载=多份证据」</td><td>FEVER 证据标注 + Veracity 透明度实践 <a class="cite" href="#r1">[1]</a><a class="cite" href="#r3">[3]</a></td></tr>
    <tr><td>事实核查分级标签</td><td>supported / refuted / mixed / insufficient 等受约束标签</td><td>FEVER 三类标签；PolitiFact 六档；FactCheck.org / Full Fact 规范 <a class="cite" href="#r1">[1]</a><a class="cite" href="#r13">[13]</a><a class="cite" href="#r14">[14]</a><a class="cite" href="#r15">[15]</a></td></tr>
    <tr><td>网页正文抽取</td><td>从媒体报道中抽取正文与元数据，支撑指纹比对</td><td>trafilatura，ACL-IJCNLP 2021 <a class="cite" href="#r4">[4]</a></td></tr>
    <tr><td>可信度频段</td><td>按「事实报道质量 + 编辑独立性 / 偏见」对来源分层</td><td>MBFC、Ad Fontes、NewsGuard、AllSides <a class="cite" href="#r8">[8]</a><a class="cite" href="#r10">[10]</a><a class="cite" href="#r9">[9]</a><a class="cite" href="#r11">[11]</a></td></tr>
    <tr><td>信源可信度与认知偏差</td><td>来源加权、强制反证与缺口</td><td>Hovland & Weiss 1951；Nickerson 1998 <a class="cite" href="#r5">[5]</a><a class="cite" href="#r6">[6]</a></td></tr>
    <tr><td>公众信任度研究</td><td>作为媒体排序的背景依据</td><td>Reuters Institute《Digital News Report》，牛津大学 <a class="cite" href="#r12">[12]</a></td></tr>
  </table>
</section>

<section id="bands">
  <h2>五、为什么用「频段体系」，它从哪里来</h2>
  <p>「频段」指把媒体按可信度 / 偏见放在连续区间上分层，而不是简单分成「真 / 假」两类。这套做法来自多家公开评级机构与研究的成熟实践，NewsVerify 把它们的方法论综合为排序思路：</p>
  <ul>
    <li><b>Media Bias/Fact Check（MBFC）</b>：用 Very High / High / Mostly Factual / Mixed / Low / Very Low 六级事实报道评级，并单列 Extreme Left → Least Biased → Extreme Right 偏见刻度。NewsVerify 的 <code>factual</code> 字段参考此口径。<a class="cite" href="#r8">[8]</a></li>
    <li><b>Ad Fontes Media（Media Bias Chart®）</b>：把媒体放在「偏见（横轴）× 可靠性（纵轴）」二维坐标上，形如「频段」。<a class="cite" href="#r10">[10]</a></li>
    <li><b>NewsGuard</b>：依九条新闻可信标准给出评级（不反复发布虚假内容、有纠错机制、区分新闻与观点、披露所有权与资金等）。<a class="cite" href="#r9">[9]</a></li>
    <li><b>AllSides</b>：以左 / 中 / 右偏见频谱标注媒体与新闻。<a class="cite" href="#r11">[11]</a></li>
    <li><b>Reuters Institute（牛津大学）</b>《Digital News Report》：提供跨国家公众媒体信任度数据，说明信任因国家与群体而异。<a class="cite" href="#r12">[12]</a></li>
  </ul>
  <p>NewsVerify 不购买或转售这些机构的授权数据，也不伪造它们的分数；只把<b>公开方法论</b>作为排序思路，并在未获授权处标注 <span class="tag">not_connected</span> / <span class="tag">context_only</span>。</p>
</section>

<section id="diagram">
  <h2>六、整套体系图示（来源讲解）</h2>
  <p>下图自顶向下展示「理论依据 → 核查方法 → 评级研究 → 系统流水线 → 输出评价」的完整链路，节点中的 <tspan fill="#34d399" font-size="10">[n]</tspan> 对应文末引用源注释。</p>
  <svg viewBox="0 0 960 640" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="NewsVerify 理论与数据体系图">
    <defs>
      <linearGradient id="gg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#38bdf8"/><stop offset="1" stop-color="#818cf8"/></linearGradient>
      <marker id="ar" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#38bdf8"/></marker>
    </defs>
    <!-- Band A -->
    <text x="20" y="24" fill="#818cf8" font-size="13" font-weight="800">① 理论依据 · 为什么这样做</text>
    <g font-size="11" fill="#e6edf7">
      <rect x="20" y="34" width="290" height="52" rx="9" fill="#141d38" stroke="#818cf8"/>
      <text x="165" y="54" text-anchor="middle">真理理论：符合 / 融贯 / 验证</text>
      <text x="165" y="72" text-anchor="middle" fill="#8b9bb5">Stanford Encyclopedia of Philosophy</text>
      <text x="290" y="82" text-anchor="end" fill="#34d399" font-size="10">[7]</text>
      <rect x="330" y="34" width="290" height="52" rx="9" fill="#141d38" stroke="#818cf8"/>
      <text x="475" y="54" text-anchor="middle">信源可信度理论（耶鲁 1951）</text>
      <text x="475" y="72" text-anchor="middle" fill="#8b9bb5">Hovland &amp; Weiss · 来源分层依据</text>
      <text x="600" y="82" text-anchor="end" fill="#34d399" font-size="10">[5]</text>
      <rect x="640" y="34" width="300" height="52" rx="9" fill="#141d38" stroke="#818cf8"/>
      <text x="790" y="54" text-anchor="middle">确认偏误（Tufts 1998）</text>
      <text x="790" y="72" text-anchor="middle" fill="#8b9bb5">Nickerson · 强制反证与缺口</text>
      <text x="920" y="82" text-anchor="end" fill="#34d399" font-size="10">[6]</text>
    </g>
    <!-- arrows A->B -->
    <g stroke="#38bdf8" stroke-width="1.4" marker-end="url(#ar)" fill="none">
      <path d="M480,86 L480,112"/>
    </g>
    <!-- Band B -->
    <text x="20" y="132" fill="#818cf8" font-size="13" font-weight="800">② 核查方法 · 怎么做（可复现）</text>
    <g font-size="11" fill="#e6edf7">
      <rect x="20" y="142" width="225" height="56" rx="9" fill="#111c33" stroke="#38bdf8"/>
      <text x="132" y="162" text-anchor="middle">FEVER · NAACL 2018</text>
      <text x="132" y="179" text-anchor="middle" fill="#8b9bb5">主张分解 · 受约束标签</text>
      <text x="227" y="193" text-anchor="end" fill="#34d399" font-size="10">[1]</text>
      <rect x="255" y="142" width="225" height="56" rx="9" fill="#111c33" stroke="#38bdf8"/>
      <text x="367" y="162" text-anchor="middle">AVeriTeC · NeurIPS 2023</text>
      <text x="367" y="179" text-anchor="middle" fill="#8b9bb5">真实网页证据 · 多步论证</text>
      <text x="462" y="193" text-anchor="end" fill="#34d399" font-size="10">[2]</text>
      <rect x="490" y="142" width="225" height="56" rx="9" fill="#111c33" stroke="#38bdf8"/>
      <text x="602" y="162" text-anchor="middle">Veracity · 2025</text>
      <text x="602" y="179" text-anchor="middle" fill="#8b9bb5">透明 · 可解释 · 多语言</text>
      <text x="697" y="193" text-anchor="end" fill="#34d399" font-size="10">[3]</text>
      <rect x="725" y="142" width="215" height="56" rx="9" fill="#111c33" stroke="#38bdf8"/>
      <text x="832" y="162" text-anchor="middle">trafilatura · ACL 2021</text>
      <text x="832" y="179" text-anchor="middle" fill="#8b9bb5">网页正文抽取 · 指纹</text>
      <text x="922" y="193" text-anchor="end" fill="#34d399" font-size="10">[4]</text>
    </g>
    <g stroke="#38bdf8" stroke-width="1.4" marker-end="url(#ar)" fill="none"><path d="M480,198 L480,222"/></g>
    <!-- Band C -->
    <text x="20" y="242" fill="#818cf8" font-size="13" font-weight="800">③ 评级与信任研究 · 先看谁</text>
    <g font-size="11" fill="#e6edf7">
      <rect x="20" y="252" width="185" height="54" rx="9" fill="#162240" stroke="#818cf8"/>
      <text x="112" y="272" text-anchor="middle">MBFC</text><text x="112" y="289" text-anchor="middle" fill="#8b9bb5">事实质量 × 偏见</text><text x="188" y="300" text-anchor="end" fill="#34d399" font-size="10">[8]</text>
      <rect x="215" y="252" width="185" height="54" rx="9" fill="#162240" stroke="#818cf8"/>
      <text x="307" y="272" text-anchor="middle">Ad Fontes</text><text x="307" y="289" text-anchor="middle" fill="#8b9bb5">偏见 × 可靠性坐标</text><text x="382" y="300" text-anchor="end" fill="#34d399" font-size="10">[10]</text>
      <rect x="410" y="252" width="185" height="54" rx="9" fill="#162240" stroke="#818cf8"/>
      <text x="502" y="272" text-anchor="middle">NewsGuard</text><text x="502" y="289" text-anchor="middle" fill="#8b9bb5">九条可信标准</text><text x="577" y="300" text-anchor="end" fill="#34d399" font-size="10">[9]</text>
      <rect x="605" y="252" width="165" height="54" rx="9" fill="#162240" stroke="#818cf8"/>
      <text x="687" y="272" text-anchor="middle">AllSides</text><text x="687" y="289" text-anchor="middle" fill="#8b9bb5">偏见频谱</text><text x="752" y="300" text-anchor="end" fill="#34d399" font-size="10">[11]</text>
      <rect x="780" y="252" width="160" height="54" rx="9" fill="#162240" stroke="#818cf8"/>
      <text x="860" y="272" text-anchor="middle">Reuters Institute</text><text x="860" y="289" text-anchor="middle" fill="#8b9bb5">公众信任度</text><text x="922" y="300" text-anchor="end" fill="#34d399" font-size="10">[12]</text>
    </g>
    <text x="20" y="326" fill="#8b9bb5" font-size="10">标签与规范参考：PolitiFact [13] · FactCheck.org [14] · Full Fact [15] · Google ClaimReview [16]</text>
    <g stroke="#38bdf8" stroke-width="1.4" marker-end="url(#ar)" fill="none"><path d="M480,330 L480,352"/></g>
    <!-- Band D pipeline -->
    <text x="20" y="372" fill="#34d399" font-size="13" font-weight="800">④ NewsVerify 核查流水线 · 组合落地</text>
    <g font-size="11" fill="#08101f" font-weight="800">
      <rect x="20" y="382" width="145" height="42" rx="9" fill="url(#gg)"/><text x="92" y="408" text-anchor="middle">① 拆原子主张</text>
      <rect x="177" y="382" width="145" height="42" rx="9" fill="url(#gg)"/><text x="249" y="408" text-anchor="middle">② 多源检索 + RSS</text>
      <rect x="334" y="382" width="145" height="42" rx="9" fill="url(#gg)"/><text x="406" y="408" text-anchor="middle">③ 白名单 + 独立性</text>
      <rect x="491" y="382" width="145" height="42" rx="9" fill="url(#gg)"/><text x="563" y="408" text-anchor="middle">④ 受约束判定</text>
      <rect x="648" y="382" width="145" height="42" rx="9" fill="url(#gg)"/><text x="720" y="408" text-anchor="middle">⑤ Top30 交叉核查</text>
      <rect x="805" y="382" width="135" height="42" rx="9" fill="url(#gg)"/><text x="872" y="408" text-anchor="middle">⑥ 持续追踪</text>
    </g>
    <g stroke="#38bdf8" stroke-width="1.3" marker-end="url(#ar)" fill="none">
      <path d="M165,403 L175,403"/><path d="M322,403 L332,403"/><path d="M479,403 L489,403"/><path d="M636,403 L646,403"/><path d="M793,403 L803,403"/>
    </g>
    <g stroke="#38bdf8" stroke-width="1.4" marker-end="url(#ar)" fill="none"><path d="M480,424 L480,452"/></g>
    <!-- Band E output -->
    <text x="20" y="472" fill="#34d399" font-size="13" font-weight="800">⑤ 输出与评价 · 可审计</text>
    <g font-size="11" fill="#e6edf7">
      <rect x="20" y="482" width="300" height="58" rx="9" fill="#0a1a16" stroke="#34d399"/>
      <text x="170" y="503" text-anchor="middle">带出处的判定结论</text>
      <text x="170" y="521" text-anchor="middle" fill="#8b9bb5">标签 / 置信度 / 反证 / 缺口 / 原文 URL</text>
      <rect x="330" y="482" width="300" height="58" rx="9" fill="#0a1a16" stroke="#34d399"/>
      <text x="480" y="503" text-anchor="middle">可信度频段排序 + 白名单</text>
      <text x="480" y="521" text-anchor="middle" fill="#8b9bb5">Top30 媒体 · 事实等级 · 允许 / 拒绝</text>
      <rect x="640" y="482" width="300" height="58" rx="9" fill="#1f1a3a" stroke="#f59e0b"/>
      <text x="790" y="503" text-anchor="middle">学术界与全球评价</text>
      <text x="790" y="521" text-anchor="middle" fill="#8b9bb5">FEVER / AVeriTeC 评测 · DNR 信任度</text>
    </g>
    <text x="480" y="580" text-anchor="middle" fill="#8b9bb5" font-size="11">哲学层定形态 → 认知层防偏差 → 方法层给流程 → 机构层定排序；四层在此汇合为可追溯的结论</text>
    <text x="480" y="606" text-anchor="middle" fill="#8b9bb5" font-size="10">引用编号 [1]–[16] 详见文末「引用源注释」，均附原文地址与最早发表机构</text>
  </svg>
</section>

<section id="academia">
  <h2>七、在学术界与全球评价中的位置</h2>
  <h3>学术脉络</h3>
  <p>自动事实核查是 NLP 与新闻学的交叉领域。FEVER 确立了「检索—验证」范式并用 185,445 条维基百科派生主张建立可评测基准<a class="cite" href="#r1">[1]</a>；AVeriTeC 将其推进到 4,568 条真实世界声明、50 家核查机构的证据与论证，并规避时间泄漏<a class="cite" href="#r2">[2]</a>；Veracity 则把透明、可解释与媒体素养作为开源系统的核心目标<a class="cite" href="#r3">[3]</a>。NewsVerify 的工程流水线正是这些范式的落地：不追求「一句话定罪」，而是输出可追溯的证据链与保留缺口。</p>
  <h3>全球评价与局限</h3>
  <ul>
    <li>路透新闻研究院《Digital News Report》持续跟踪多国公众媒体信任差异，说明「信任」因国家与群体而异——因此系统把信任度作为背景而非绝对评分。<a class="cite" href="#r12">[12]</a></li>
    <li>MBFC / NewsGuard / Ad Fontes / AllSides 等评级体系方法不同、口径不同，业界并无单一权威排名；系统的 Top30 是综合参考，明确标注「非官方名次」。<a class="cite" href="#r8">[8]</a><a class="cite" href="#r9">[9]</a><a class="cite" href="#r10">[10]</a><a class="cite" href="#r11">[11]</a></li>
    <li>模型判定具概率性，学界强调应把结论与证据、缺口并读；系统据此强制输出反证与证据缺口，避免误导。<a class="cite" href="#r6">[6]</a><a class="cite" href="#r3">[3]</a></li>
    <li>百科类站点（Wikipedia / Britannica）在本页仅用于概念背景说明，<b>不作为系统证据来源</b>（见可信来源白名单）。<a class="cite" href="#r17">[17]</a></li>
  </ul>
  <div class="callout">本页所有外部链接指向各机构 / 论文的公开页面及其原文地址；系统不使用任何未经授权的商业评级数据，不伪造评分，也不把百科站纳入证据池。</div>
</section>

<section id="sources">
  <h2>八、引用源注释（原文地址 · 最早发表机构 · 理论依据）</h2>
  <p>以下逐条对应正文的 <a class="cite" href="#r1">[n]</a> 引用编号。每条给出完整出处、<b>最早发表机构</b>、可点击的原文地址（多个来源全部列出），以及该来源提供的<b>理论依据</b>与在系统中的用途。</p>
  <ol class="reflist">
    <li id="r1">
      <div class="rt">[1] FEVER — 事实抽取与验证数据集</div>
      <div class="meta">James Thorne, Andreas Vlachos, Christos Christodoulopoulos, Arpit Mittal. <i>FEVER: a large-scale dataset for Fact Extraction and VERification</i>. <b>最早发表机构：Association for Computational Linguistics (ACL)，NAACL-HLT 2018</b>（New Orleans，2018 年 6 月）；预印本 2018-03-14。185,445 条主张，标签 Supported / Refuted / NotEnoughInfo。</div>
      <div class="u">原文（arXiv）：<a href="https://arxiv.org/abs/1803.05355" target="_blank" rel="noopener">https://arxiv.org/abs/1803.05355</a></div>
      <div class="u">DOI：<a href="https://doi.org/10.48550/arXiv.1803.05355" target="_blank" rel="noopener">https://doi.org/10.48550/arXiv.1803.05355</a></div>
      <div class="u">官方项目页：<a href="https://fever.ai/" target="_blank" rel="noopener">https://fever.ai/</a></div>
      <div class="why"><b>理论依据：</b>确立「主张分解 → 证据检索 → 受约束标签」的可复现核查范式，并保留「证据不足」类。<b>系统用途：</b>核查流水线核心与标签体系来源。</div>
    </li>
    <li id="r2">
      <div class="rt">[2] AVeriTeC — 真实世界声明验证数据集</div>
      <div class="meta">Michael Schlichtkrull, Zhijiang Guo, Andreas Vlachos. <i>AVeriTeC: A Dataset for Real-world Claim Verification with Evidence from the Web</i>. <b>最早发表机构：NeurIPS 2023 Datasets &amp; Benchmarks Track</b>；预印本 2023-05-22（剑桥大学 / 华为）。4,568 条真实声明，覆盖 50 家核查机构，含问答式证据与文本论证，规避时间泄漏。</div>
      <div class="u">原文（arXiv）：<a href="https://arxiv.org/abs/2305.13117" target="_blank" rel="noopener">https://arxiv.org/abs/2305.13117</a></div>
      <div class="u">DOI：<a href="https://doi.org/10.48550/arXiv.2305.13117" target="_blank" rel="noopener">https://doi.org/10.48550/arXiv.2305.13117</a></div>
      <div class="why"><b>理论依据：</b>把核查从人工主张推进到真实网页证据、多步问答与论证链，并强调证据时序。<b>系统用途：</b>证据链、报道时间与避免事后证据倒推。</div>
    </li>
    <li id="r3">
      <div class="rt">[3] Veracity — 开源 AI 事实核查系统</div>
      <div class="meta">Taylor Lynn Curtis, Maximilian Puelma Touzel, William Garneau, et al. <i>Veracity: An Open-Source AI Fact-Checking System</i>. <b>最早发表：arXiv 2025-06-18</b>（演示论文，多机构合作团队）。</div>
      <div class="u">原文（arXiv）：<a href="https://arxiv.org/abs/2506.15794" target="_blank" rel="noopener">https://arxiv.org/abs/2506.15794</a></div>
      <div class="u">DOI：<a href="https://doi.org/10.48550/arXiv.2506.15794" target="_blank" rel="noopener">https://doi.org/10.48550/arXiv.2506.15794</a></div>
      <div class="why"><b>理论依据：</b>强调 LLM + 网页检索的透明、可解释、多语言核查与媒体素养。<b>系统用途：</b>来源透明度、三语文档与可审计设计取向。</div>
    </li>
    <li id="r4">
      <div class="rt">[4] trafilatura — 网页正文抽取工具</div>
      <div class="meta">Adrien Barbaresi. <i>Trafilatura: A Web Scraping Library and Command-Line Tool for Text Discovery and Extraction</i>. <b>最早发表机构：Association for Computational Linguistics (ACL)，ACL-IJCNLP 2021 System Demonstrations</b>，pp. 122–131。其前身 <i>Generic Web Content Extraction with Open-Source Software</i> 发表于 KONVENS 2019。</div>
      <div class="u">原文（ACL Anthology）：<a href="https://aclanthology.org/2021.acl-demo.15/" target="_blank" rel="noopener">https://aclanthology.org/2021.acl-demo.15/</a></div>
      <div class="u">DOI：<a href="https://doi.org/10.18653/v1/2021.acl-demo.15" target="_blank" rel="noopener">https://doi.org/10.18653/v1/2021.acl-demo.15</a></div>
      <div class="u">代码仓库：<a href="https://github.com/adbar/trafilatura" target="_blank" rel="noopener">https://github.com/adbar/trafilatura</a></div>
      <div class="why"><b>理论依据：</b>给出从网页中稳定抽取正文与元数据的开源方法与评测基线。<b>系统用途：</b>证据预处理、指纹比对与独立性链折叠的工程前提。</div>
    </li>
    <li id="r5">
      <div class="rt">[5] 信源可信度理论（来源可信度实证奠基研究）</div>
      <div class="meta">Carl I. Hovland, Walter Weiss. <i>The Influence of Source Credibility on Communication Effectiveness</i>. <b>最早发表机构：Yale University（作者）；Public Opinion Quarterly, Vol. 15, No. 4, Winter 1951</b>，pp. 635–650（Oxford Academic，代表 AAPOR 出版），1951-01-01。</div>
      <div class="u">DOI：<a href="https://doi.org/10.1086/266350" target="_blank" rel="noopener">https://doi.org/10.1086/266350</a></div>
      <div class="u">原文（Oxford Academic）：<a href="https://academic.oup.com/poq/article-abstract/15/4/635/1923117" target="_blank" rel="noopener">https://academic.oup.com/poq/article-abstract/15/4/635/1923117</a></div>
      <div class="why"><b>理论依据：</b>首次以实验证明「来源可信度」显著影响内容说服效果，并提出睡眠者效应。<b>系统用途：</b>来源分层与可信度加权的学术起点，解释「为什么不能所有来源等权」。</div>
    </li>
    <li id="r6">
      <div class="rt">[6] 确认偏误（Confirming Bias）综述</div>
      <div class="meta">Raymond S. Nickerson. <i>Confirmation Bias: A Ubiquitous Phenomenon in Many Guises</i>. <b>最早发表机构：Tufts University（作者）；Review of General Psychology, Vol. 2, No. 2, 1998</b>，pp. 175–220（American Psychological Association 出版）。</div>
      <div class="u">DOI：<a href="https://doi.org/10.1037/1089-2680.2.2.175" target="_blank" rel="noopener">https://doi.org/10.1037/1089-2680.2.2.175</a></div>
      <div class="why"><b>理论依据：</b>系统梳理「人倾向寻找 / 解读支持既有信念的证据」的普遍现象。<b>系统用途：</b>强制输出反证与证据缺口，抵消单向取证偏差。</div>
    </li>
    <li id="r7">
      <div class="rt">[7] 真理理论（哲学基础）</div>
      <div class="meta">Michael Glanzberg. <i>Truth</i>. <b>最早发表机构：The Stanford Encyclopedia of Philosophy，Metaphysics Research Lab, Stanford University</b>；主编 Edward N. Zalta &amp; Uri Nodelman；条目首发 2006-06-13，实质修订 2025-06-27。</div>
      <div class="u">原文：<a href="https://plato.stanford.edu/entries/truth/" target="_blank" rel="noopener">https://plato.stanford.edu/entries/truth/</a></div>
      <div class="why"><b>理论依据：</b>系统梳理符合论、融贯论、实用 / 探究论、验证主义等主要真理理论。<b>系统用途：</b>解释为何以「证据链 + 置信度 + 缺口」逼近真实性，而非宣称绝对真伪。</div>
    </li>
    <li id="r8">
      <div class="rt">[8] Media Bias/Fact Check（MBFC）</div>
      <div class="meta">Media Bias/Fact Check. <b>机构：MBFC（美国独立媒体评级网站）</b>。方法页说明六级事实报道评级（Very High / High / Mostly Factual / Mixed / Low / Very Low）与左右偏见刻度；2025-01-01 起采用更新方法。</div>
      <div class="u">原文（方法页）：<a href="https://mediabiasfactcheck.com/methodology/" target="_blank" rel="noopener">https://mediabiasfactcheck.com/methodology/</a></div>
      <div class="why"><b>理论依据：</b>把「事实报道质量」与「政治偏见」拆成可独立评定的两个维度。<b>系统用途：</b><code>factual</code> 字段与可信度频段口径参考。</div>
    </li>
    <li id="r9">
      <div class="rt">[9] NewsGuard</div>
      <div class="meta">NewsGuard Technologies. <b>机构：2018 年由 Steven Brill 与 L. Gordon Crovitz 创立</b>。以九条可信标准评估网站（不反复发布虚假内容、有纠错机制、区分新闻与观点、披露所有权与资金、标注广告、披露负责人与利益冲突、作者可追溯等）。</div>
      <div class="u">官方主页：<a href="https://www.newsguardtech.com/" target="_blank" rel="noopener">https://www.newsguardtech.com/</a></div>
      <div class="why"><b>理论依据：</b>以编辑规范与机构透明度为核心的九维可信标准。<b>系统用途：</b>可信度频段中「编辑独立性 / 透明度」维度的参考。</div>
    </li>
    <li id="r10">
      <div class="rt">[10] Ad Fontes Media — Media Bias Chart®</div>
      <div class="meta">Ad Fontes Media, Inc. <b>机构：Ad Fontes Media（美国媒体评级机构）</b>。方法页说明以「政治偏见（横轴）× 可靠性（纵轴）」二维坐标对新闻源评级，可靠性考量 Expression / Veracity / Headline 等，偏见考量 Political Position / Language / Comparison 等。</div>
      <div class="u">原文（方法页）：<a href="https://adfontesmedia.com/methodology/" target="_blank" rel="noopener">https://adfontesmedia.com/methodology/</a></div>
      <div class="why"><b>理论依据：</b>「偏见 × 可靠性」二维模型，即「频段 / 坐标」形态的直接来源。<b>系统用途：</b>Top30「事实质量 + 偏见」分层思路。</div>
    </li>
    <li id="r11">
      <div class="rt">[11] AllSides</div>
      <div class="meta">AllSides. <b>机构：AllSides（美国媒体偏见评级机构）</b>。以左 / 中左 / 中 / 中右 / 右的偏见频谱标注媒体与新闻，并提供多视角对照。</div>
      <div class="u">官方主页：<a href="https://www.allsides.com/" target="_blank" rel="noopener">https://www.allsides.com/</a></div>
      <div class="why"><b>理论依据：</b>以偏见频谱而非真伪二分来标注媒体。<b>系统用途：</b>可信度频段中偏见维度的参考。</div>
    </li>
    <li id="r12">
      <div class="rt">[12] Reuters Institute — Digital News Report</div>
      <div class="meta">Reuters Institute for the Study of Journalism, University of Oxford. <b>最早发表机构：牛津大学路透新闻研究院</b>。年度《Digital News Report》调查多国公众对媒体与新闻的信任度与使用习惯。</div>
      <div class="u">原文（报告页）：<a href="https://www.reutersinstitute.politics.ox.ac.uk/digital-news-report" target="_blank" rel="noopener">https://www.reutersinstitute.politics.ox.ac.uk/digital-news-report</a></div>
      <div class="why"><b>理论依据：</b>公众信任因国家与群体而异的跨国民调证据。<b>系统用途：</b>把信任度作为背景参考而非绝对评分。</div>
    </li>
    <li id="r13">
      <div class="rt">[13] PolitiFact — Truth-O-Meter</div>
      <div class="meta">PolitiFact. <b>机构：2007 年由 Tampa Bay Times 创立，2018 年 2 月起由 Poynter Institute 拥有</b>。Truth-O-Meter 六档标签：True / Mostly True / Half True / Mostly False / False / Pants on Fire。</div>
      <div class="u">官方主页：<a href="https://www.politifact.com/" target="_blank" rel="noopener">https://www.politifact.com/</a></div>
      <div class="why"><b>理论依据：</b>把核查结论落在有序、公开的分级标签上，便于公众理解。<b>系统用途：</b>分级标签体系的机构范例。</div>
    </li>
    <li id="r14">
      <div class="rt">[14] FactCheck.org</div>
      <div class="meta">FactCheck.org. <b>最早发表机构：University of Pennsylvania 的 Annenberg Public Policy Center</b>，2003 年 12 月上线，由 Brooks Jackson 创办、Kathleen Hall Jamieson 推动，主要由 Annenberg Foundation 资助。</div>
      <div class="u">官方主页：<a href="https://www.factcheck.org/" target="_blank" rel="noopener">https://www.factcheck.org/</a></div>
      <div class="why"><b>理论依据：</b>大学附属、非营利的公开核查与纠错规范。<b>系统用途：</b>分级标签与「可追溯、可纠错」流程的机构范例。</div>
    </li>
    <li id="r15">
      <div class="rt">[15] Full Fact</div>
      <div class="meta">Full Fact. <b>机构：英国独立事实核查慈善机构，2009 年成立、2010 年上线，2014 年取得慈善资格，总部伦敦</b>。原则：事实准确、以证据支撑、公开纠错；提供核查方法、AI 工具与批判性思维培训。</div>
      <div class="u">原文（机构介绍）：<a href="https://fullfact.org/about/" target="_blank" rel="noopener">https://fullfact.org/about/</a></div>
      <div class="u">核查方法：<a href="https://fullfact.org/about/how-we-fact-check/" target="_blank" rel="noopener">https://fullfact.org/about/how-we-fact-check/</a></div>
      <div class="why"><b>理论依据：</b>以透明、纠错与公众判断为核心的核查伦理。<b>系统用途：</b>「结论 + 证据 + 缺口并读、便于外部复核」的方法参照。</div>
    </li>
    <li id="r16">
      <div class="rt">[16] Google Fact Check Tools / ClaimReview</div>
      <div class="meta">Google. <b>机构：Google（Fact Check Tools API 与 ClaimReview 结构化数据标准发布方）</b>。Claim Search API 可查询 Fact Check Explorer 中的核查结果；ClaimReview 标记使核查结论可机器读取。</div>
      <div class="u">原文（API 文档）：<a href="https://developers.google.com/fact-check/tools/api" target="_blank" rel="noopener">https://developers.google.com/fact-check/tools/api</a></div>
      <div class="u">ClaimReview 标准：<a href="https://developers.google.com/search/docs/appearance/structured-data/factcheck" target="_blank" rel="noopener">https://developers.google.com/search/docs/appearance/structured-data/factcheck</a></div>
      <div class="why"><b>理论依据：</b>核查结论的可机读、可聚合标准。<b>系统用途：</b>结论附来源类型与原文 URL，便于外部工具复核与聚合。</div>
    </li>
    <li id="r17">
      <div class="rt">[17] Wikipedia / Britannica（仅概念背景，非证据来源）</div>
      <div class="meta">Wikipedia、Encyclopaedia Britannica. <b>机构：Wikimedia Foundation / Encyclopaedia Britannica, Inc.</b>。仅用于本页个别概念的背景说明。</div>
      <div class="u">Wikipedia：<a href="https://en.wikipedia.org/" target="_blank" rel="noopener">https://en.wikipedia.org/</a></div>
      <div class="u">Britannica：<a href="https://www.britannica.com/" target="_blank" rel="noopener">https://www.britannica.com/</a></div>
      <div class="why"><b>理论依据：</b>通用概念背景。<b>系统用途：</b>明确排除——百科站<b>不作为系统证据来源</b>（见可信来源白名单）。</div>
    </li>
  </ol>
</section>

<div class="footer">NewsVerify · 理性查看新闻理论来源 · 本页为公开说明，随版本更新 · 引用编号 [1]–[17] 及原文地址均列于上节</div>
</div></body></html>"""
