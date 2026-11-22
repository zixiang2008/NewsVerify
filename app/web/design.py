"""NewsVerify Design System (NVDS).

A self-contained, offline-safe design framework shared by every page:
console, login / registration, admin and the API console.

Design principles
-----------------
* One token set: all colours come from the 9 CSS themes below, so a theme
  change instantly restyles every component and every page.
* Layered surfaces: mesh background, glass bars and elevated cards create
  depth without images or external fonts.
* Calm hierarchy: uppercase kickers, tabular numbers, generous spacing and
  restrained colour for a professional evidence-workspace feel.
* Motion with intent: short easing on interactive elements, fade-rise on
  page entry, and a full ``prefers-reduced-motion`` escape hatch.

No CDN, no build step, no web fonts -- everything works on an offline NAS.
"""

from __future__ import annotations

THEME_CSS = r""":root{
 color-scheme:dark;
 --bg:rgb(8 16 31);--bg2:rgb(13 22 40);--card:rgb(17 28 51);--card2:rgb(22 34 64);
 --surface-0:rgb(8 16 31);--surface-1:rgb(17 28 51);--surface-2:rgb(11 22 40);--surface-3:rgb(22 34 64);
 --text:rgb(230 237 247);--muted:rgb(139 155 181);--border:rgb(30 45 77);
 --accent:rgb(56 189 248);--accent2:rgb(129 140 248);--accent3:rgb(52 211 153);
 --accent-soft:rgb(125 211 252);--accent2-soft:rgb(165 180 252);
 --ok:rgb(34 197 94);--warn:rgb(245 158 11);--bad:rgb(239 68 68);
 --ok-text:rgb(74 222 128);--warn-text:rgb(251 191 36);--bad-text:rgb(248 113 113);
 --on-accent:rgb(8 16 31);--hero-a:rgb(26 42 74);--hero-b:rgb(31 26 58);--reported-bg:rgb(10 26 22);
 --shadow:0 14px 40px rgba(0,0,0,.38);--radius:16px;--radius-sm:10px;--gap:18px;
}
html[data-theme="paper"]{
 color-scheme:light;
 --bg:rgb(244 247 252);--bg2:rgb(236 241 249);--card:rgb(255 255 255);--card2:rgb(248 250 253);
 --surface-0:rgb(248 250 253);--surface-1:rgb(255 255 255);--surface-2:rgb(240 244 250);--surface-3:rgb(232 238 247);
 --text:rgb(24 37 58);--muted:rgb(95 111 133);--border:rgb(211 220 233);
 --accent:rgb(37 99 235);--accent2:rgb(79 70 229);--accent3:rgb(13 148 136);
 --accent-soft:rgb(29 78 216);--accent2-soft:rgb(67 56 202);
 --ok:rgb(22 163 74);--warn:rgb(217 119 6);--bad:rgb(220 38 38);
 --ok-text:rgb(21 128 61);--warn-text:rgb(180 83 9);--bad-text:rgb(190 18 60);
 --on-accent:rgb(255 255 255);--hero-a:rgb(219 234 254);--hero-b:rgb(224 231 255);--reported-bg:rgb(236 253 245);
 --shadow:0 12px 34px rgba(30,58,95,.10);
}
html[data-theme="slate"]{
 color-scheme:dark;
 --bg:rgb(15 23 42);--bg2:rgb(20 30 52);--card:rgb(30 41 59);--card2:rgb(36 48 68);
 --surface-0:rgb(15 23 42);--surface-1:rgb(30 41 59);--surface-2:rgb(24 35 54);--surface-3:rgb(40 53 74);
 --text:rgb(241 245 249);--muted:rgb(148 163 184);--border:rgb(51 65 85);
 --accent:rgb(96 165 250);--accent2:rgb(167 139 250);--accent3:rgb(45 212 191);
 --accent-soft:rgb(147 197 253);--accent2-soft:rgb(196 181 253);
 --ok:rgb(74 222 128);--warn:rgb(251 191 36);--bad:rgb(248 113 113);
 --ok-text:rgb(134 239 172);--warn-text:rgb(253 224 71);--bad-text:rgb(252 165 165);
 --on-accent:rgb(15 23 42);--hero-a:rgb(30 58 95);--hero-b:rgb(49 46 129);--reported-bg:rgb(20 58 48);
 --shadow:0 16px 40px rgba(2,6,23,.45);
}
html[data-theme="terminal"]{
 color-scheme:dark;
 --bg:rgb(5 14 9);--bg2:rgb(8 20 13);--card:rgb(10 26 17);--card2:rgb(13 32 21);
 --surface-0:rgb(5 14 9);--surface-1:rgb(10 26 17);--surface-2:rgb(8 22 14);--surface-3:rgb(16 38 25);
 --text:rgb(220 255 233);--muted:rgb(134 175 150);--border:rgb(34 82 54);
 --accent:rgb(74 222 128);--accent2:rgb(163 230 53);--accent3:rgb(45 212 191);
 --accent-soft:rgb(134 239 172);--accent2-soft:rgb(190 242 100);
 --ok:rgb(74 222 128);--warn:rgb(250 204 21);--bad:rgb(248 113 113);
 --ok-text:rgb(134 239 172);--warn-text:rgb(253 224 71);--bad-text:rgb(252 165 165);
 --on-accent:rgb(5 14 9);--hero-a:rgb(10 45 25);--hero-b:rgb(20 60 35);--reported-bg:rgb(10 40 24);
 --shadow:0 16px 42px rgba(0,0,0,.55);--radius:10px;--radius-sm:6px;
}
html[data-theme="terminal"] body{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace}
/* ==== v0.6.0 新增 5 套风格：ocean / forest / sunset / violet / mono ==== */
html[data-theme="ocean"]{
 color-scheme:dark;
 --bg:rgb(4 20 32);--bg2:rgb(6 30 46);--card:rgb(8 40 58);--card2:rgb(10 48 68);
 --surface-0:rgb(6 32 48);--surface-1:rgb(8 40 58);--surface-2:rgb(7 36 53);--surface-3:rgb(12 54 76);
 --text:rgb(224 246 252);--muted:rgb(128 178 196);--border:rgb(22 78 102);
 --accent:rgb(34 211 238);--accent2:rgb(56 189 248);--accent3:rgb(45 212 191);
 --accent-soft:rgb(103 232 249);--accent2-soft:rgb(125 211 252);
 --ok:rgb(45 212 191);--warn:rgb(251 146 60);--bad:rgb(244 114 182);
 --ok-text:rgb(94 234 212);--warn-text:rgb(253 186 116);--bad-text:rgb(249 168 212);
 --on-accent:rgb(4 20 32);--hero-a:rgb(8 65 92);--hero-b:rgb(15 45 80);--reported-bg:rgb(8 52 52);
 --shadow:0 16px 42px rgba(0,20,32,.5);
}
html[data-theme="forest"]{
 color-scheme:dark;
 --bg:rgb(10 22 16);--bg2:rgb(14 32 22);--card:rgb(18 42 29);--card2:rgb(22 50 34);
 --surface-0:rgb(14 34 23);--surface-1:rgb(18 42 29);--surface-2:rgb(16 38 26);--surface-3:rgb(26 58 39);
 --text:rgb(232 246 235);--muted:rgb(150 182 158);--border:rgb(44 84 57);
 --accent:rgb(132 204 22);--accent2:rgb(163 230 53);--accent3:rgb(52 211 153);
 --accent-soft:rgb(190 242 100);--accent2-soft:rgb(217 249 157);
 --ok:rgb(74 222 128);--warn:rgb(234 179 8);--bad:rgb(248 113 113);
 --ok-text:rgb(134 239 172);--warn-text:rgb(253 224 71);--bad-text:rgb(252 165 165);
 --on-accent:rgb(10 22 16);--hero-a:rgb(20 68 38);--hero-b:rgb(30 58 26);--reported-bg:rgb(20 52 34);
 --shadow:0 16px 42px rgba(6,20,12,.5);
}
html[data-theme="sunset"]{
 color-scheme:dark;
 --bg:rgb(30 16 26);--bg2:rgb(44 22 32);--card:rgb(58 30 40);--card2:rgb(70 36 46);
 --surface-0:rgb(44 24 33);--surface-1:rgb(58 30 40);--surface-2:rgb(50 27 37);--surface-3:rgb(84 44 54);
 --text:rgb(255 238 236);--muted:rgb(196 152 158);--border:rgb(110 58 70);
 --accent:rgb(251 146 60);--accent2:rgb(244 114 182);--accent3:rgb(250 204 21);
 --accent-soft:rgb(253 186 116);--accent2-soft:rgb(249 168 212);
 --ok:rgb(74 222 128);--warn:rgb(250 204 21);--bad:rgb(248 113 113);
 --ok-text:rgb(134 239 172);--warn-text:rgb(253 224 71);--bad-text:rgb(252 165 165);
 --on-accent:rgb(30 16 26);--hero-a:rgb(120 40 50);--hero-b:rgb(90 30 70);--reported-bg:rgb(60 30 35);
 --shadow:0 16px 42px rgba(30,10,20,.5);
}
html[data-theme="violet"]{
 color-scheme:dark;
 --bg:rgb(16 12 32);--bg2:rgb(24 18 48);--card:rgb(34 26 64);--card2:rgb(42 32 76);
 --surface-0:rgb(24 18 46);--surface-1:rgb(34 26 64);--surface-2:rgb(29 22 55);--surface-3:rgb(52 40 92);
 --text:rgb(240 236 255);--muted:rgb(160 150 200);--border:rgb(70 56 120);
 --accent:rgb(192 132 252);--accent2:rgb(129 140 248);--accent3:rgb(232 121 249);
 --accent-soft:rgb(216 180 254);--accent2-soft:rgb(165 180 252);
 --ok:rgb(74 222 128);--warn:rgb(251 191 36);--bad:rgb(248 113 113);
 --ok-text:rgb(134 239 172);--warn-text:rgb(253 224 71);--bad-text:rgb(252 165 165);
 --on-accent:rgb(16 12 32);--hero-a:rgb(76 29 149);--hero-b:rgb(49 46 129);--reported-bg:rgb(40 30 70);
 --shadow:0 16px 42px rgba(16,8,32,.55);
}
html[data-theme="mono"]{
 color-scheme:light;
 --bg:rgb(250 250 248);--bg2:rgb(240 240 236);--card:rgb(255 255 253);--card2:rgb(246 246 242);
 --surface-0:rgb(248 248 244);--surface-1:rgb(255 255 253);--surface-2:rgb(238 238 233);--surface-3:rgb(228 228 222);
 --text:rgb(28 28 26);--muted:rgb(108 108 102);--border:rgb(204 204 196);
 --accent:rgb(55 65 81);--accent2:rgb(87 83 78);--accent3:rgb(71 85 105);
 --accent-soft:rgb(55 65 81);--accent2-soft:rgb(87 83 78);
 --ok:rgb(22 101 52);--warn:rgb(154 88 5);--bad:rgb(190 18 60);
 --ok-text:rgb(22 101 52);--warn-text:rgb(154 88 5);--bad-text:rgb(190 18 60);
 --on-accent:rgb(255 255 253);--hero-a:rgb(232 232 226);--hero-b:rgb(240 238 230);--reported-bg:rgb(232 244 236);
 --shadow:0 12px 34px rgba(20,20,18,.10);
}
html[data-theme="mono"] body{font-family:Georgia,"Times New Roman",serif}"""

# ---------------------------------------------------------------------------
# Component library + enhancement layer
# ---------------------------------------------------------------------------
DESIGN_CSS = r"""
/* ===== NVDS 1.0 — foundations ===== */
:root{
  --nvds-font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  --nvds-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
  --nvds-xs:10px; --nvds-sm:11px; --nvds-md:12px; --nvds-base:13px; --nvds-lg:15px; --nvds-xl:19px; --nvds-2xl:26px; --nvds-3xl:36px;
  --nvds-1:4px; --nvds-2:8px; --nvds-3:12px; --nvds-4:16px; --nvds-5:20px; --nvds-6:24px; --nvds-8:32px; --nvds-10:40px;
  --nvds-r-sm:10px; --nvds-r:14px; --nvds-r-lg:20px; --nvds-r-xl:26px;
  --nvds-ease: cubic-bezier(.22,.7,.24,1);
  --nvds-t: .18s var(--nvds-ease);
  --nvds-glass: color-mix(in srgb, var(--surface-1) 82%, transparent);
  --nvds-line: color-mix(in srgb, var(--border) 70%, transparent);
  --nvds-glow: 0 0 0 3px color-mix(in srgb, var(--accent) 16%, transparent);
}
html{scroll-behavior:smooth}
body{font-family:var(--nvds-font);font-size:var(--nvds-base);line-height:1.6;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
::selection{background:color-mix(in srgb,var(--accent) 32%,transparent);color:var(--text)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
a{color:var(--accent)}

/* Mesh ambience — two soft colour fields + a faint dot grid */
.nvds-ambient{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden}
.nvds-ambient::before,.nvds-ambient::after{content:"";position:absolute;border-radius:50%;filter:blur(80px);opacity:.5}
.nvds-ambient::before{width:52vw;height:52vw;left:-14vw;top:-22vw;background:var(--hero-a);animation:nvds-float-a 26s ease-in-out infinite alternate}
.nvds-ambient::after{width:46vw;height:46vw;right:-12vw;top:-14vw;background:var(--hero-b);animation:nvds-float-b 32s ease-in-out infinite alternate}
.nvds-grid{position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.35;
  background-image:radial-gradient(circle at 1px 1px,var(--border) 1px,transparent 0);background-size:26px 26px;
  mask-image:linear-gradient(to bottom,#000 0,transparent 70%)}
@keyframes nvds-float-a{from{transform:translate3d(0,0,0) scale(1)}to{transform:translate3d(6vw,5vh,0) scale(1.12)}}
@keyframes nvds-float-b{from{transform:translate3d(0,0,0) scale(1.06)}to{transform:translate3d(-5vw,7vh,0) scale(.95)}}

/* Surface primitives */
.nvds-card{position:relative;background:linear-gradient(155deg,color-mix(in srgb,var(--card) 94%,transparent),var(--card2));
  border:1px solid var(--nvds-line);border-radius:var(--nvds-r-lg);box-shadow:var(--shadow);overflow:hidden}
.nvds-card::before{content:"";position:absolute;inset:0 0 auto;height:1px;background:linear-gradient(90deg,transparent,color-mix(in srgb,var(--accent) 45%,transparent),transparent)}
.nvds-card-pad{padding:var(--nvds-6)}
.nvds-kicker{font-size:var(--nvds-xs);letter-spacing:2.4px;text-transform:uppercase;color:var(--accent);font-weight:800}
.nvds-title{font-size:var(--nvds-xl);font-weight:750;letter-spacing:-.2px;line-height:1.3}
.nvds-sub{color:var(--muted);font-size:var(--nvds-md);line-height:1.65}
.nvds-mono{font-family:var(--nvds-mono)}

/* Buttons */
.nvds-btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:10px 18px;border-radius:var(--nvds-r-sm);
  border:1px solid transparent;background:linear-gradient(110deg,var(--accent),var(--accent2));color:var(--on-accent);
  font-size:var(--nvds-base);font-weight:750;cursor:pointer;transition:var(--nvds-t);text-decoration:none;white-space:nowrap}
.nvds-btn:hover{transform:translateY(-1px);box-shadow:0 8px 22px color-mix(in srgb,var(--accent) 26%,transparent);filter:saturate(1.08)}
.nvds-btn:active{transform:translateY(0)}
.nvds-btn.soft{background:color-mix(in srgb,var(--accent) 13%,var(--card));color:var(--accent);border-color:color-mix(in srgb,var(--accent) 30%,transparent)}
.nvds-btn.ghost{background:transparent;color:var(--muted);border-color:var(--border)}
.nvds-btn.ghost:hover{color:var(--accent);border-color:var(--accent);box-shadow:none}
.nvds-btn.sm{padding:6px 12px;font-size:var(--nvds-sm)}
.nvds-btn.block{width:100%}
.nvds-btn-row{display:flex;gap:8px;flex-wrap:wrap}

/* Inputs */
.nvds-field{display:flex;flex-direction:column;gap:6px;margin-bottom:var(--nvds-4)}
.nvds-label{font-size:var(--nvds-sm);color:var(--muted);font-weight:650;display:flex;justify-content:space-between;gap:8px}
.nvds-input,.nvds-select,.nvds-textarea{width:100%;background:var(--surface-0);border:1px solid var(--border);border-radius:var(--nvds-r-sm);
  color:var(--text);padding:10px 12px;font-size:var(--nvds-base);font-family:inherit;outline:none;transition:var(--nvds-t)}
.nvds-input:focus,.nvds-select:focus,.nvds-textarea:focus{border-color:var(--accent);box-shadow:var(--nvds-glow)}
.nvds-input.center{text-align:center;letter-spacing:6px;font-family:var(--nvds-mono);font-weight:700}
.nvds-textarea{min-height:96px;resize:vertical;line-height:1.65}
.nvds-hint{font-size:var(--nvds-xs);color:var(--muted);line-height:1.6}

/* Chips / badges */
.nvds-chip{display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;font-size:var(--nvds-xs);font-weight:700;
  background:color-mix(in srgb,var(--accent) 12%,transparent);color:var(--accent);border:1px solid color-mix(in srgb,var(--accent) 25%,transparent)}
.nvds-chip.ok{background:color-mix(in srgb,var(--ok) 14%,transparent);color:var(--ok-text);border-color:color-mix(in srgb,var(--ok) 28%,transparent)}
.nvds-chip.warn{background:color-mix(in srgb,var(--warn) 14%,transparent);color:var(--warn-text);border-color:color-mix(in srgb,var(--warn) 28%,transparent)}
.nvds-chip.bad{background:color-mix(in srgb,var(--bad) 14%,transparent);color:var(--bad-text);border-color:color-mix(in srgb,var(--bad) 28%,transparent)}
.nvds-chip.mute{background:var(--surface-2);color:var(--muted);border-color:var(--border)}

/* Tables */
.nvds-table{width:100%;border-collapse:separate;border-spacing:0;font-size:var(--nvds-md)}
.nvds-table th{text-align:left;color:var(--muted);font-size:var(--nvds-xs);letter-spacing:.6px;text-transform:uppercase;
  padding:10px 12px;border-bottom:1px solid var(--border);white-space:nowrap}
.nvds-table td{padding:11px 12px;border-bottom:1px solid var(--nvds-line);vertical-align:middle}
.nvds-table tr:last-child td{border-bottom:none}
.nvds-table tbody tr{transition:background var(--nvds-t)}
.nvds-table tbody tr:hover{background:color-mix(in srgb,var(--accent) 5%,transparent)}
.nvds-code{font-family:var(--nvds-mono);font-size:var(--nvds-sm);color:var(--accent);word-break:break-all}
.nvds-scroll{overflow:auto;scrollbar-width:thin;scrollbar-color:var(--accent) var(--surface-2)}
.nvds-scroll::-webkit-scrollbar{width:8px;height:8px}
.nvds-scroll::-webkit-scrollbar-thumb{background:linear-gradient(180deg,var(--accent),var(--accent2));border-radius:8px}
.nvds-scroll::-webkit-scrollbar-track{background:var(--surface-2);border-radius:8px}

/* Code blocks with copy affordance */
.nvds-codebox{position:relative;background:var(--surface-0);border:1px solid var(--border);border-radius:var(--nvds-r);
  padding:14px 14px 12px;margin-top:8px}
.nvds-codebox pre{margin:0;font-family:var(--nvds-mono);font-size:var(--nvds-sm);line-height:1.7;color:var(--text);
  white-space:pre-wrap;word-break:break-word;max-height:320px;overflow:auto}
.nvds-codebox .nvds-copy{position:absolute;right:8px;top:8px}
.nvds-codebox .nvds-cap{font-size:var(--nvds-xs);color:var(--muted);margin-bottom:6px;font-weight:700;letter-spacing:.5px}

/* Copy button + toast */
.nvds-copy{border:1px solid var(--border);background:var(--surface-2);color:var(--muted);border-radius:8px;
  padding:4px 9px;font-size:var(--nvds-xs);cursor:pointer;transition:var(--nvds-t)}
.nvds-copy:hover{color:var(--accent);border-color:var(--accent)}
.nvds-copy.done{color:var(--ok-text);border-color:var(--ok)}
.nvds-toast{position:fixed;left:50%;bottom:28px;transform:translate(-50%,16px);z-index:99;background:var(--card);
  border:1px solid var(--accent);color:var(--text);padding:10px 18px;border-radius:999px;box-shadow:var(--shadow);
  font-size:var(--nvds-md);opacity:0;pointer-events:none;transition:opacity .22s,transform .22s}
.nvds-toast.show{opacity:1;transform:translate(-50%,0)}

/* Tabs, steps, empty */
.nvds-tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:var(--nvds-4)}
.nvds-tab{padding:7px 14px;border-radius:999px;border:1px solid var(--border);background:var(--surface-2);
  color:var(--muted);font-size:var(--nvds-md);cursor:pointer;transition:var(--nvds-t)}
.nvds-tab:hover{color:var(--accent);border-color:var(--accent)}
.nvds-tab.active{background:linear-gradient(110deg,var(--accent),var(--accent2));color:var(--on-accent);border-color:transparent;font-weight:750}
.nvds-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-top:var(--nvds-4)}
.nvds-step{background:var(--surface-0);border:1px solid var(--border);border-radius:var(--nvds-r);padding:14px;position:relative}
.nvds-step .num{position:absolute;right:12px;top:10px;font-size:var(--nvds-2xl);font-weight:850;color:color-mix(in srgb,var(--accent) 15%,transparent);line-height:1}
.nvds-step b{display:block;font-size:var(--nvds-base);color:var(--text);margin-bottom:4px}
.nvds-step span{font-size:var(--nvds-sm);color:var(--muted);line-height:1.6}
.nvds-empty{padding:36px;text-align:center;color:var(--muted);font-size:var(--nvds-md)}
.nvds-alert{padding:11px 14px;border-radius:var(--nvds-r-sm);font-size:var(--nvds-md);line-height:1.7;margin:10px 0;
  background:color-mix(in srgb,var(--accent) 9%,var(--surface-0));border:1px solid color-mix(in srgb,var(--accent) 24%,transparent);color:var(--text)}
.nvds-alert.bad{background:color-mix(in srgb,var(--bad) 10%,var(--surface-0));border-color:color-mix(in srgb,var(--bad) 30%,transparent);color:var(--bad-text)}
.nvds-alert.ok{background:color-mix(in srgb,var(--ok) 10%,var(--surface-0));border-color:color-mix(in srgb,var(--ok) 30%,transparent);color:var(--ok-text)}

/* Entry animation */
.nvds-rise{animation:nvds-rise .5s var(--nvds-ease) both}
.nvds-rise.d1{animation-delay:.06s}.nvds-rise.d2{animation-delay:.12s}.nvds-rise.d3{animation-delay:.18s}
@keyframes nvds-rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}

/* ===== Console enhancement layer (keeps all existing class names) ===== */
body>.nvds-ambient,body>.nvds-grid{position:fixed}
.wrap{position:relative;z-index:1}
header.topbar{position:sticky;top:0;z-index:30;padding:14px 18px;margin:-24px -24px 20px;border-radius:0;
  background:var(--nvds-glass);backdrop-filter:blur(18px) saturate(140%);-webkit-backdrop-filter:blur(18px) saturate(140%);
  border-bottom:1px solid var(--nvds-line)}
header.topbar::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:1px;
  background:linear-gradient(90deg,transparent,color-mix(in srgb,var(--accent) 55%,transparent),color-mix(in srgb,var(--accent2) 40%,transparent),transparent)}
.logo{position:relative;border-radius:14px;box-shadow:var(--shadow),inset 0 1px 0 rgba(255,255,255,.18);transition:var(--nvds-t)}
.logo:hover{transform:rotate(-4deg) scale(1.04)}
h1{letter-spacing:-.4px;font-weight:780}
.brand .kicker{font-family:var(--nvds-mono)}
.nav{position:sticky;top:82px;z-index:25;background:var(--nvds-glass);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border-color:var(--nvds-line);box-shadow:0 8px 24px color-mix(in srgb,var(--surface-0) 40%,transparent)}
.nav a{position:relative;font-weight:600}
.nav a:hover{background:color-mix(in srgb,var(--accent) 12%,transparent);color:var(--accent)}
.version-btn,.music-btn,.theme-switch{box-shadow:inset 0 1px 0 rgba(255,255,255,.05)}
.stats .card{position:relative;overflow:hidden;padding:18px 20px;transition:var(--nvds-t)}
.stats .card::before{content:"";position:absolute;left:0;right:0;top:0;height:2px;
  background:linear-gradient(90deg,var(--accent),var(--accent2),transparent)}
.stats .card:hover{transform:translateY(-3px);border-color:color-mix(in srgb,var(--accent) 40%,transparent);box-shadow:0 18px 44px rgba(0,0,0,.28)}
.stat .n{font-size:38px;letter-spacing:-1px;font-variant-numeric:tabular-nums}
.panel{position:relative;transition:border-color var(--nvds-t)}
.panel:hover{border-color:color-mix(in srgb,var(--accent) 22%,var(--border))}
.panel h2{letter-spacing:-.2px}
.panel h2 .icon{box-shadow:inset 0 1px 0 rgba(255,255,255,.12)}
.hitem{border-radius:var(--nvds-r-sm);border-bottom:1px solid var(--nvds-line);position:relative;transition:var(--nvds-t)}
.hitem::before{content:"";position:absolute;left:0;top:10px;bottom:10px;width:2px;border-radius:2px;background:transparent;transition:var(--nvds-t)}
.hitem:hover::before{background:var(--accent)}
.hitem:hover{padding-left:18px;background:color-mix(in srgb,var(--accent) 5%,transparent)}
.media-item{border-radius:var(--nvds-r-sm);transition:var(--nvds-t)}
.media-item:hover{transform:translateX(-2px)}
.btn,.mini-btn,.tab{box-shadow:inset 0 1px 0 rgba(255,255,255,.06)}
textarea:focus,select:focus,input:focus{border-color:var(--accent);box-shadow:var(--nvds-glow)}
.modal-bg{backdrop-filter:blur(8px)}
.modal{border-radius:var(--nvds-r-xl);animation:nvds-pop .26s var(--nvds-ease) both}
@keyframes nvds-pop{from{opacity:0;transform:translateY(14px) scale(.985)}to{opacity:1;transform:none}}
.footer{border-top:1px solid var(--nvds-line)}

/* ===== Auth pages ===== */
.nvds-auth{min-height:100vh;display:grid;place-items:center;padding:32px 18px;position:relative;z-index:1}
.nvds-auth-card{width:min(440px,100%);padding:34px 34px 26px;animation:nvds-rise .55s var(--nvds-ease) both}
.nvds-auth-head{text-align:center;margin-bottom:24px}
.nvds-auth-logo{width:56px;height:56px;margin:0 auto 14px;border-radius:18px;display:grid;place-items:center;
  background:linear-gradient(140deg,var(--accent),var(--accent2));color:var(--on-accent);font-weight:850;font-size:20px;
  box-shadow:0 12px 30px color-mix(in srgb,var(--accent) 32%,transparent),inset 0 1px 0 rgba(255,255,255,.25)}
.nvds-auth-head h1{font-size:22px;margin:2px 0 4px}
.nvds-auth-head p{color:var(--muted);font-size:var(--nvds-md)}
.nvds-auth-foot{margin-top:18px;text-align:center;color:var(--muted);font-size:var(--nvds-md)}
.nvds-auth-foot a{text-decoration:none;font-weight:700}
.nvds-auth-foot a:hover{text-decoration:underline}
.nvds-sep{display:flex;align-items:center;gap:10px;color:var(--muted);font-size:var(--nvds-xs);margin:16px 0}
.nvds-sep::before,.nvds-sep::after{content:"";flex:1;height:1px;background:var(--border)}

/* ===== Admin / API console shell ===== */
.nvds-shell{max-width:1360px;margin:0 auto;padding:26px 24px 48px;position:relative;z-index:1}
.nvds-top{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;margin-bottom:20px}
.nvds-crumb{font-size:var(--nvds-sm);color:var(--muted);margin-bottom:6px}
.nvds-crumb a{text-decoration:none}
.nvds-crumb a:hover{text-decoration:underline}
.nvds-tabsbar{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:20px;padding:6px;border-radius:var(--nvds-r);
  background:var(--surface-1);border:1px solid var(--nvds-line)}
.nvds-tabsbar a{padding:8px 14px;border-radius:10px;color:var(--muted);text-decoration:none;font-size:var(--nvds-md);font-weight:600;transition:var(--nvds-t)}
.nvds-tabsbar a:hover{background:var(--surface-2);color:var(--accent)}
.nvds-tabsbar a.active{background:linear-gradient(110deg,var(--accent),var(--accent2));color:var(--on-accent);font-weight:750}
.nvds-grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.nvds-grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.nvds-side{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(300px,.65fr);gap:16px;align-items:start}
@media(max-width:1000px){.nvds-grid2,.nvds-side,.nvds-grid3{grid-template-columns:1fr}}
.nvds-panel-head{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.nvds-panel-head h2{font-size:var(--nvds-lg);font-weight:750;letter-spacing:-.2px}
.nvds-kv{display:grid;grid-template-columns:150px 1fr;gap:8px 14px;font-size:var(--nvds-md)}
.nvds-kv .k{color:var(--muted)}
.nvds-kv .v{word-break:break-all}
.nvds-flex{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.nvds-grow{flex:1;min-width:0}
.nvds-divider{height:1px;background:var(--nvds-line);margin:18px 0}
.nvds-status{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--muted);margin-right:7px}
.nvds-status.on{background:var(--ok);box-shadow:0 0 8px color-mix(in srgb,var(--ok) 70%,transparent)}
.nvds-status.off{background:var(--bad)}
.nvds-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--accent);margin:0 3px}

@media(prefers-reduced-motion:reduce){
  *,*::before,*::after{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important;scroll-behavior:auto!important}
}

/* ===== NVDS mobile layer — phone-first refinements =====
   Kept at the end of DESIGN_CSS so every page that inherits the design
   system gets the same touch-friendly behaviour. Page-specific overrides
   are appended after this block by their own templates. */
@media(max-width:720px){
  html{-webkit-text-size-adjust:100%}
  body{font-size:14px;line-height:1.65}
  .nvds-ambient::before{width:78vw;height:78vw;left:-28vw;top:-30vw;filter:blur(54px);opacity:.36}
  .nvds-ambient::after{width:70vw;height:70vw;right:-26vw;top:-20vw;filter:blur(54px);opacity:.32}
  .nvds-grid{background-size:20px 20px;opacity:.22}
  .nvds-shell{padding:16px 12px calc(28px + env(safe-area-inset-bottom,0px))}
  .nvds-top{gap:10px;margin-bottom:14px}
  .nvds-crumb{font-size:11px;line-height:1.5}
  .nvds-tabsbar{flex-wrap:nowrap;overflow-x:auto;gap:4px;padding:5px;scrollbar-width:none;-webkit-overflow-scrolling:touch}
  .nvds-tabsbar::-webkit-scrollbar{display:none}
  .nvds-tabsbar a{flex:0 0 auto;padding:9px 12px;font-size:12px;white-space:nowrap}
  .nvds-card-pad{padding:16px}
  .nvds-title{font-size:17px}
  .nvds-sub{font-size:12px}
  .nvds-panel-head{gap:8px;margin-bottom:12px}
  .nvds-panel-head h2{font-size:15px}
  .nvds-kv{grid-template-columns:1fr;gap:1px 0}
  .nvds-kv .k{font-size:11px}
  .nvds-kv .v{font-size:12px}
  .nvds-flex{gap:8px}
  .nvds-btn{min-height:42px;padding:10px 14px;font-size:13px}
  .nvds-btn.sm{min-height:34px;padding:7px 10px;font-size:11px}
  .nvds-input,.nvds-select,.nvds-textarea{font-size:16px;padding:11px 12px}
  .nvds-input.center{letter-spacing:4px}
  .nvds-textarea{min-height:88px}
  .nvds-codebox{padding:12px}
  .nvds-codebox pre{max-height:220px;font-size:11px}
  .nvds-toast{bottom:calc(16px + env(safe-area-inset-bottom,0px));max-width:calc(100vw - 32px);text-align:center}
  .nvds-steps{grid-template-columns:1fr;gap:8px}
  .nvds-step{padding:12px}
  .nvds-step .num{font-size:22px}
  .nvds-table{font-size:11px}
  .nvds-table th,.nvds-table td{padding:8px}
  .nvds-scroll{-webkit-overflow-scrolling:touch}
  .nvds-auth{padding:20px 12px calc(20px + env(safe-area-inset-bottom,0px));align-items:start}
  .nvds-auth-card{padding:24px 20px 20px;border-radius:18px}
  .nvds-auth-head{margin-bottom:18px}
  .nvds-auth-head h1{font-size:20px}
  .nvds-auth-logo{width:50px;height:50px;font-size:18px}
  .nvds-auth-foot{font-size:12px}
  .nvds-grid2,.nvds-grid3,.nvds-side{grid-template-columns:1fr;gap:12px}
  .nvds-divider{margin:14px 0}
}
@media(max-width:400px){
  .nvds-btn-row .nvds-btn{flex:1 1 100%}
  .nvds-auth-card{padding:20px 16px}
}
"""

# ---------------------------------------------------------------------------
# Shared page shell
# ---------------------------------------------------------------------------
SHELL_JS = r"""
function nvToast(msg){var t=document.getElementById('nvdsToast');if(!t)return;t.textContent=msg;t.classList.add('show');clearTimeout(window.__nvToastT);window.__nvToastT=setTimeout(function(){t.classList.remove('show')},2200);}
async function nvCopy(text,btn){
  try{await navigator.clipboard.writeText(text);}catch(e){
    var a=document.createElement('textarea');a.value=text;document.body.appendChild(a);a.select();
    try{document.execCommand('copy');}catch(_){}a.remove();
  }
  nvToast('已复制到剪贴板');
  if(btn){var old=btn.textContent;btn.textContent='✓ 已复制';btn.classList.add('done');setTimeout(function(){btn.textContent=old;btn.classList.remove('done')},1600);}
}
function nvCopyEls(sel){document.querySelectorAll(sel).forEach(function(b){b.addEventListener('click',function(){nvCopy(b.getAttribute('data-copy')||'',b);});});}
function nvApplyTheme(key){if(key)document.documentElement.setAttribute('data-theme',key);try{localStorage.setItem('nv_theme',key)}catch(e){}}
(function(){try{var t=localStorage.getItem('nv_theme');if(t)document.documentElement.setAttribute('data-theme',t);}catch(e){}})();
"""


def page_shell(
    title: str,
    body: str,
    *,
    extra_css: str = "",
    extra_js: str = "",
    body_class: str = "",
) -> str:
    """Wrap page content with the full NVDS token set, ambient background and helpers."""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>{title}</title>
<style>{THEME_CSS}{DESIGN_CSS}{extra_css}</style></head>
<body class="{body_class}">
<div class="nvds-ambient"></div><div class="nvds-grid"></div>
{body}
<div class="nvds-toast" id="nvdsToast"></div>
<script>{SHELL_JS}{extra_js}</script>
</body></html>"""


def tabs_html(active: str, base: str = "/admin") -> str:
    items = [
        ("overview", "⚙️ 总览", base),
        ("accounts", "👥 账号与邀请码", base + "/accounts"),
        ("api", "🔌 API 管理与调试", base + "/api"),
        ("im", "💬 IM 接入向导", base + "/im"),
    ]
    links = "".join(
        f'<a href="{href}" class="{("active" if key == active else "")}">{label}</a>'
        for key, label, href in items
    )
    return f'<nav class="nvds-tabsbar">{links}<a href="/" style="margin-left:auto">← 返回控制台</a></nav>'
