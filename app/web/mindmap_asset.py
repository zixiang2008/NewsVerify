"""Shared mind-map CSS/JS assets.

Used both by the authenticated console (app.py) and by the public share page,
so a shared map looks and behaves exactly the same for its recipient.
Embedded as text because the application deliberately serves a single-file UI
(no build step, no CDN dependency) so it can run on an offline NAS.
"""

import json


CSS = r"""
/* ==== v0.7.3 脑图引擎：SVG 连线 / 三种布局 / 分享 ==== */
.mm-toolbar{display:flex;gap:7px;flex-wrap:wrap;align-items:center;margin:10px 0}
.mm-toolbar .mm-sep{width:1px;height:18px;background:var(--border);margin:0 2px}
.mm-layout-btn{background:var(--surface-1);border:1px solid var(--border);color:var(--muted);
  border-radius:8px;padding:5px 10px;font-size:11px;cursor:pointer;transition:.15s}
.mm-layout-btn:hover{border-color:var(--accent);color:var(--accent)}
.mm-layout-btn.active{background:linear-gradient(135deg,var(--accent),var(--accent2));color:var(--on-accent);
  border-color:transparent;font-weight:700}
.mm-stage{position:relative;overflow:auto;background:
  radial-gradient(circle at 1px 1px,var(--border) 1px,transparent 0) 0 0/22px 22px,
  var(--surface-0);border:1px solid var(--border);border-radius:14px;padding:12px;
  min-height:220px;max-height:62vh}
.mm-stage.mini{min-height:104px;max-height:none;padding:4px;border-radius:10px;cursor:pointer}
.mm-viewport{position:relative;margin:0 auto}
.mm-graph{position:relative;transform-origin:0 0}
.mm-links{position:absolute;left:0;top:0;overflow:visible;pointer-events:none}
.mm-node{position:absolute;display:flex;flex-direction:column;justify-content:center;gap:2px;
  padding:5px 10px;background:var(--card);border:1px solid var(--border);
  border-left:4px solid var(--mmc,var(--accent));border-radius:10px;overflow:hidden;
  color:var(--text);box-shadow:0 4px 14px rgba(0,0,0,.16);user-select:none;transition:border-color .15s,transform .15s}
.mm-node:hover{border-color:var(--mmc,var(--accent));transform:translateY(-1px)}
.mm-node.mm-branch-node{cursor:pointer}
.mm-node.mm-leaf{background:var(--surface-1);border-left-width:3px}
.mm-node.mm-root{background:linear-gradient(135deg,var(--accent),var(--accent2));color:var(--on-accent);
  border:none;border-radius:13px;box-shadow:var(--shadow);cursor:pointer;text-align:center;align-items:center}
.mm-node.mm-root .mm-s{color:var(--on-accent);opacity:.88}
.mm-node.mm-leaf a{color:var(--accent);text-decoration:none;display:block;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.mm-node.mm-leaf a:hover{text-decoration:underline}
.mm-t{font-size:12px;font-weight:700;line-height:1.35;display:-webkit-box;-webkit-line-clamp:2;
  -webkit-box-orient:vertical;overflow:hidden;word-break:break-word}
.mm-s{font-size:10px;color:var(--muted);line-height:1.3;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mm-node.done{border-left-color:var(--ok)}
.mm-node.active{border-left-color:var(--accent)}
.mm-node.fail{border-left-color:var(--bad)}
.mm-node.lit{border-left-color:var(--accent3)}
.mm-arrow{display:inline-block;min-width:11px;opacity:.7}
.mm-badge{display:inline-block;font-size:9px;padding:1px 6px;border-radius:999px;font-weight:700;margin-left:4px}
.mm-badge.b-done{background:rgba(34,197,94,.18);color:var(--ok-text)}
.mm-badge.b-active{background:rgba(56,189,248,.18);color:var(--accent-soft)}
.mm-badge.b-fail{background:rgba(239,68,68,.18);color:var(--bad-text)}
.mm-badge.b-track{background:rgba(167,139,250,.2);color:var(--accent2-soft)}
.mm-legend{display:flex;gap:12px;flex-wrap:wrap;margin-top:8px;font-size:10px;color:var(--muted)}
.mm-legend span{display:flex;align-items:center;gap:5px}
.mm-legend i{width:16px;height:3px;border-radius:3px;display:inline-block}
.mm-hint{font-size:10px;color:var(--muted);margin:6px 0}
.mm-stage.mini .mm-t{font-size:10px;-webkit-line-clamp:1}
.mm-stage.mini .mm-s{font-size:9px}
.mm-stage.mini .mm-node{padding:3px 7px;border-left-width:3px;border-radius:8px}
.mm-overview-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-top:10px}
.mm-ov-card{background:var(--surface-0);border:1px solid var(--border);border-radius:12px;padding:12px;cursor:pointer;transition:.15s}
.mm-ov-card:hover{border-color:var(--accent);transform:translateY(-1px)}
.mm-ov-card .ov-t{font-weight:700;font-size:12px;color:var(--text);line-height:1.4}
.mm-ov-card .ov-m{color:var(--muted);font-size:10px;margin-top:6px}
.mm-progress{height:4px;border-radius:999px;background:var(--border);margin-top:8px;overflow:hidden}
.mm-progress>i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent3))}
.mm-mini-wrap{border-top:1px dashed var(--border);margin-top:8px;padding-top:6px}
.mm-mini-head{display:flex;justify-content:space-between;align-items:center;font-size:10px;color:var(--muted);margin-bottom:4px}
.mm-share-bg{position:fixed;inset:0;background:rgba(3,8,20,.72);display:flex;align-items:center;
  justify-content:center;z-index:9999;padding:18px}
.mm-share-box{background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:20px;width:min(520px,94vw);box-shadow:var(--shadow);color:var(--text)}
.mm-share-box h3{font-size:16px;color:var(--accent);margin-bottom:8px}
.mm-share-box input{width:100%;background:var(--surface-0);border:1px solid var(--border);
  color:var(--text);border-radius:9px;padding:9px 10px;font-size:12px;margin:8px 0}
.mm-share-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.mm-share-qr{display:flex;justify-content:center;margin-top:10px}
.mm-share-qr img{background:#fff;border-radius:10px;padding:8px;width:156px;height:156px}
.mm-share-note{font-size:10px;color:var(--muted);line-height:1.6;margin-top:10px}
.share-shell{max-width:1180px;margin:0 auto;padding:22px}
.share-shell header{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.share-shell h1{font-size:20px;color:var(--accent)}
.share-shell .sub{color:var(--muted);font-size:12px;margin:6px 0 14px}
.share-shell .mm-stage{max-height:70vh;min-height:420px}
@media(max-width:640px){.share-shell{padding:12px}.mm-stage{min-height:280px}}
"""

JS = r"""
/* ===== NewsVerify mind-map engine v0.7.3 =====
   One model -> three layouts (tree / waterfall / radial), SVG bezier links,
   inline per-news maps, exports and anonymous share links. No external libs. */
const MM_COLORS=['var(--accent)','var(--accent2)','var(--accent3)','rgb(167 139 250)','rgb(245 158 11)','rgb(244 114 182)'];
const MM_LEGEND=['主张与判定','证据与溯源','媒体覆盖','持续追踪','处理进度','任务历史'];
const MM_SIZE={root:[218,64],branch:[188,56],leaf:[236,54]};
const MM_MINI_SIZE={root:[176,38],branch:[150,34],leaf:[176,34]};
let _mmLayout='tree',_mmExpanded={},_mmModel=null,_mmTarget=null,_mmScale=1,_mmRenderCache={};
try{_mmLayout=localStorage.getItem('nv_mm_layout')||'tree';}catch(e){}
function mmEsc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function mmColor(c){
  c=String(c||'var(--accent)');
  const m=/var\((--[a-zA-Z0-9-]+)\)/.exec(c);
  if(!m)return c;
  return (getComputedStyle(document.documentElement).getPropertyValue(m[1])||'').trim()||'#38bdf8';
}
function mmBadge(b){
  if(!b)return '';
  return '<span class="mm-badge '+(b.cls||'')+'">'+mmEsc(b.text)+'</span>';
}
/* ---------- model builders ---------- */
function mmVerdictInfo(v){
  if(!v)return null;
  const label=String(v.label||'');
  return {text:label,cls:label==='supported'?'b-done':(label==='refuted'?'b-fail':'b-active')};
}
function mmModelFromDetail(d){
  d=d||{};
  const claims=d.claims||[],jobs=d.jobs||[],subs=d.subscriptions||[],notes=d.notifications||[];
  const jr=(jobs[0]&&jobs[0].result)||{};
  const st=(jobs[0]&&jobs[0].status)||d.status||'unknown';
  const done=st==='done',run=(st==='running'||st==='queued');
  const verdict=(claims.find(c=>c.verdict)||{}).verdict;
  const act=subs.filter(s=>s.active&&!s.paused);
  const model={eventId:d.id||'',root:{
    id:'root',title:'📰 '+mmEsc(String(d.title||'未命名新闻').slice(0,30)),
    sub:mmEsc((verdict?verdict.label+' · ':'')+claims.length+' 主张 · '+(d.media_hits||0)+'/30 媒体'+(act.length?' · 追踪中':'')),
    action:{type:'detail',id:d.id||''}},branches:[]};

  const kids1=claims.map((c,i)=>{
    const v=c.verdict;
    return {id:'c'+i,title:mmEsc(String(c.text||'').slice(0,52)),
      sub:mmEsc('证据 '+(c.evidence||[]).length+' 条'+(v?' · 置信 '+(v.confidence*100).toFixed(0)+'%':'')),
      badge:mmVerdictInfo(v),cls:v?(v.label==='refuted'?'fail':'done'):''};
  });
  model.branches.push({id:'claims',icon:'🔬',title:'主张与判定',meta:claims.length+' 条原子主张',
    cls:done?'done':(run?'active':''),children:kids1});

  const seen=new Set(),kids2=[];
  claims.forEach(c=>(c.evidence||[]).forEach(ev=>{
    const k=ev.url||ev.domain;if(!k||seen.has(k))return;seen.add(k);
    kids2.push({id:'e'+kids2.length,title:mmEsc(String(ev.title||ev.domain||'来源').slice(0,46)),
      sub:mmEsc((ev.media_name||ev.domain||'')+(ev.media_rank?' · 榜第 '+ev.media_rank+' 名':' · 非榜单来源')),
      url:ev.url||'',cls:ev.media_rank?'lit':''});
  }));
  model.branches.push({id:'evidence',icon:'📚',title:'证据与溯源',meta:seen.size+' 个独立来源',
    cls:'lit',children:kids2});

  const tm=d.top_media||[],lit=tm.filter(m=>Number(m.hit_count||0)>0);
  const kids3=[{id:'m0',title:mmEsc(lit.length+' / '+(tm.length||30)+' 家媒体报道'),
    sub:mmEsc('共 '+(d.total_reports||0)+' 条来源'),cls:lit.length?'lit':''}];
  if(lit.length)kids3.push({id:'m1',sub:mmEsc(lit.slice(0,10).map(m=>m.name).join('、')),title:'已报道媒体'});
  model.branches.push({id:'media',icon:'🌐',title:'媒体覆盖',meta:(d.media_hits||0)+'/30 家',
    cls:d.media_hits?'lit':'',children:kids3});

  const kids4=[{id:'t0',title:act.length?mmEsc('🟢 追踪中 · 间隔 '+act[0].interval_hours+'h'):'⚪ 未开启追踪',
    sub:act.length&&act[0].next_run_at?mmEsc('下次检查 '+new Date(act[0].next_run_at).toLocaleString()):''}];
  notes.slice(0,8).forEach((n,i)=>{
    const base=String(n.content_hash||'').startsWith('baseline:');
    kids4.push({id:'t'+(i+1),title:mmEsc(n.kind&&n.kind!=='update'?n.kind:(base?'追踪已启动':'检测到更新')),
      sub:n.created_at?mmEsc(new Date(n.created_at).toLocaleString()):''});
  });
  model.branches.push({id:'track',icon:'📡',title:'持续追踪',meta:notes.length+' 条更新',
    cls:act.length?'lit':'',children:kids4});

  const prog=(jr.progress||[]);
  const kids5=prog.length?prog.map((p,i)=>({id:'p'+i,title:mmEsc(String(p.step||'').slice(0,50)),
    sub:p.time?mmEsc(new Date(p.time).toLocaleTimeString()):''})):[{id:'p0',sub:'暂无进度记录',title:'—'}];
  model.branches.push({id:'progress',icon:'⏳',title:'处理进度',meta:prog.length+' 个步骤',
    cls:done?'done':(run?'active':''),children:kids5});

  const kids6=jobs.map((j,i)=>({id:'j'+i,title:mmEsc(String(j.kind||'job')+' · '+String(j.status||'')),
    sub:(j.finished_at?mmEsc(new Date(j.finished_at).toLocaleString()):'')+(j.attempts>1?' · '+j.attempts+' 次':''),
    cls:j.status==='failed'?'fail':''}));
  model.branches.push({id:'history',icon:'🗂',title:'任务历史',meta:jobs.length+' 次执行',children:kids6});
  return model;
}
/* Compact model per card: every news item carries its own mini map. */
function mmModelFromList(e){
  e=e||{};
  const jr=e.job_result||{},vs=e.verdicts||[],v=vs[0];
  const claims=(e.claims||[]).length,subs=e.active_subs||0;
  const st=e.job_status||e.status||'',done=st==='done',run=(st==='running'||st==='queued');
  return {eventId:e.id||'',root:{id:'root',title:'📰 '+mmEsc(String(e.title||'').slice(0,26)),
    sub:mmEsc((v?v.label+' · ':'')+claims+' 主张'),action:{type:'detail',id:e.id||''}},branches:[
    {id:'v',icon:'⚖️',title:'判定',meta:v?String(v.label):'待核查',badge:mmVerdictInfo(v),cls:done?'done':(run?'active':''),children:[]},
    {id:'c',icon:'🔬',title:'主张',meta:claims+' 条',cls:claims?'done':'',children:[]},
    {id:'m',icon:'🌐',title:'媒体覆盖',meta:(jr.media_hits||0)+'/30',cls:jr.top_media?'lit':'',children:[]},
    {id:'t',icon:'📡',title:'追踪',meta:subs?('开启 '+subs):'未开启',cls:subs?'lit':'',children:[]}
  ]};
}
/* ---------- geometry ---------- */
function mmEdge(a,b){
  const dx=b.cx-a.cx,dy=b.cy-a.cy;
  if(!dx&&!dy)return {x:a.cx,y:a.cy};
  const tx=dx?a.w/2/Math.abs(dx):Infinity,ty=dy?a.h/2/Math.abs(dy):Infinity,t=Math.min(tx,ty);
  return {x:a.cx+dx*t,y:a.cy+dy*t};
}
function mmPath(p,q,layout){
  if(layout==='tree'){const mx=(p.x+q.x)/2;return 'M'+p.x+','+p.y+' C'+mx+','+p.y+' '+mx+','+q.y+' '+q.x+','+q.y;}
  if(layout==='waterfall'){const my=(p.y+q.y)/2;return 'M'+p.x+','+p.y+' C'+p.x+','+my+' '+q.x+','+my+' '+q.x+','+q.y;}
  const dx=q.x-p.x,dy=q.y-p.y;
  return 'M'+p.x+','+p.y+' C'+(p.x+dx*.45)+','+(p.y+dy*.05)+' '+(p.x+dx*.55)+','+(p.y+dy*.95)+' '+q.x+','+q.y;
}
function mmGeometry(model,layout,mini,stateKey){
  const S=mini?MM_MINI_SIZE:MM_SIZE,branches=model.branches||[];
  const nodes=[],paths=[];
  const root={id:'root',kind:'root',data:model.root||{},w:S.root[0],h:S.root[1]};
  function kidsOf(b){
    const key=stateKey+'|'+b.id;
    return _mmExpanded[key]===false?[]:(b.children||[]);
  }
  function pushNode(node){nodes.push(node);return node;}
  function link(a,b,color,dim){paths.push({a:a,b:b,color:color,dim:!!dim});}
  if(layout==='waterfall'&&!mini){
    const colW=220,gap=8,lh=54;
    const W=Math.max(branches.length*colW+80,860);
    const by=124,bh=S.branch[1],lhGap=lh+gap;
    let maxKids=0;
    branches.forEach(b=>{maxKids=Math.max(maxKids,kidsOf(b).length);});
    const H=by+bh+16+maxKids*lhGap+22;
    Object.assign(root,{cx:W/2,cy:18+S.root[1]/2});pushNode(root);
    branches.forEach((b,i)=>{
      const bn=pushNode({id:'b'+i,kind:'branch',data:b,color:i,w:S.branch[0],h:bh,
        key:stateKey+'|'+b.id,open:_mmExpanded[stateKey+'|'+b.id]!==false});
      bn.cx=40+i*colW+colW/2;bn.cy=by+bh/2;link(root,bn,i);
      kidsOf(b).forEach((k,j)=>{
        const kn=pushNode({id:'b'+i+'k'+j,kind:'leaf',data:k,color:i,w:S.leaf[0],h:lh});
        kn.cx=bn.cx;kn.cy=by+bh+16+j*lhGap+lh/2;link(bn,kn,i,true);
      });
    });
    return {nodes:nodes,paths:paths,width:W,height:H,layout:layout};
  }
  if(layout==='radial'&&!mini){
    const n=Math.max(1,branches.length),R1=205;
    let maxKids=0;branches.forEach(b=>{maxKids=Math.max(maxKids,kidsOf(b).length);});
    /* Many leaves are spread over concentric rings so labels never pile up. */
    const perRing=6,rings=Math.max(1,Math.ceil(maxKids/perRing));
    const R2=450,Rmax=R2+(rings-1)*110;
    const W=Math.max(980,2*(Rmax+S.leaf[0]/2+40)),H=W,cx=W/2,cy=H/2;
    Object.assign(root,{cx:cx,cy:cy});pushNode(root);
    branches.forEach((b,i)=>{
      const ang=-Math.PI/2+i*2*Math.PI/n;
      const bn=pushNode({id:'b'+i,kind:'branch',data:b,color:i,w:S.branch[0],h:S.branch[1],
        key:stateKey+'|'+b.id,open:_mmExpanded[stateKey+'|'+b.id]!==false});
      bn.cx=cx+R1*Math.cos(ang);bn.cy=cy+R1*Math.sin(ang);link(root,bn,i);
      const kids=kidsOf(b),span=(2*Math.PI/n)*.82;
      kids.forEach((k,j)=>{
        const ring=Math.floor(j/perRing),idx=j%perRing;
        const cnt=Math.min(perRing,kids.length-ring*perRing);
        const a=kids.length===1?ang:(ang-span/2+(idx+.5)*span/cnt);
        const rr=R2+ring*110;
        const kn=pushNode({id:'b'+i+'k'+j,kind:'leaf',data:k,color:i,w:S.leaf[0],h:S.leaf[1]});
        kn.cx=cx+rr*Math.cos(a);kn.cy=cy+rr*Math.sin(a);link(bn,kn,i,true);
      });
    });
    return {nodes:nodes,paths:paths,width:W,height:H,layout:layout};
  }
  /* default + mini: left-to-right tree */
  const lh=mini?S.leaf[1]:S.leaf[1],gap=mini?5:9,lhGap=lh+gap;
  let y=16;const groups=[];
  branches.forEach((b,i)=>{
    const kids=kidsOf(b),gh=Math.max(S.branch[1],kids.length*lhGap+6);
    groups.push({b:b,kids:kids,top:y,h:gh});y+=gh+(mini?9:18);
  });
  const H=Math.max(mini?104:220,y+10),W=mini?548:820;
  const bx=mini?206:300,lx=mini?372:548;
  Object.assign(root,{cx:18+S.root[0]/2,cy:H/2});pushNode(root);
  groups.forEach((g,i)=>{
    const bn=pushNode({id:'b'+i,kind:'branch',data:g.b,color:i,w:S.branch[0],h:S.branch[1],
      key:stateKey+'|'+g.b.id,open:_mmExpanded[stateKey+'|'+g.b.id]!==false});
    bn.cx=bx+S.branch[0]/2;bn.cy=g.top+g.h/2;link(root,bn,i);
    g.kids.forEach((k,j)=>{
      const kn=pushNode({id:'b'+i+'k'+j,kind:'leaf',data:k,color:i,w:S.leaf[0],h:lh});
      kn.cx=lx+S.leaf[0]/2;kn.cy=g.top+3+j*lhGap+lh/2;link(bn,kn,i,true);
    });
  });
  return {nodes:nodes,paths:paths,width:W,height:H,layout:'tree'};
}
/* ---------- rendering ---------- */
function mmNodeHTML(n,opts){
  const data=n.data||{},color=MM_COLORS[n.color%MM_COLORS.length];
  const left=(n.cx-n.w/2),top=(n.cy-n.h/2);
  let cls='mm-node '+(n.kind==='root'?'mm-root':(n.kind==='leaf'?'mm-leaf':'mm-branch-node'));
  if(data.cls)cls+=' '+data.cls;
  let onclick='';
  if(n.kind==='branch'&&!opts.mini&&!opts.readonly)
    onclick=' onclick="mmToggleBranch(\''+n.key+'\')" title="点击展开/收起下级"';
  if(n.kind==='root'&&data.action&&data.action.type==='detail'&&!opts.readonly)
    onclick=' onclick="showDetail(\''+mmEsc(data.action.id)+'\')" title="查看该新闻完整详情"';
  let title=String(data.title||'');
  if(n.kind==='branch')title='<span class="mm-arrow">'+(n.open?'▾':'▸')+'</span>'+title;
  if(n.kind==='leaf'&&data.url)
    title='<a href="'+mmEsc(data.url)+'" target="_blank" rel="noopener">↗ '+title+'</a>';
  const badge=(n.kind==='root'?'':mmBadge(data.badge));
  return '<div class="'+cls+'" style="left:'+left+'px;top:'+top+'px;width:'+n.w+'px;height:'+n.h+'px;--mmc:'+color+'"'+onclick+'>'+
    '<div class="mm-t">'+title+badge+'</div>'+
    (data.sub||data.meta?'<div class="mm-s">'+mmEsc(data.sub||data.meta)+'</div>':'')+'</div>';
}
function mmRender(cid,model,layout,opts){
  opts=opts||{};layout=(opts.mini?'tree':(layout||'tree'));
  const stateKey=opts.stateKey||(model&&model.eventId)||'mm';
  const geo=mmGeometry(model||{root:{},branches:[]},layout,!!opts.mini,stateKey);
  const scale=opts.mini?1:Math.max(.5,Math.min(1.6,_mmScale));
  const defs='<defs>'+MM_COLORS.map((c,i)=>'<marker id="mm-arrow-'+i+'" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto">'+
    '<path d="M0,0 L7,3.5 L0,7 Z" fill="'+mmColor(c)+'"/></marker>').join('')+'</defs>';
  const paths=geo.paths.map(p=>{
    const a=mmEdge(p.a,p.b),b=mmEdge(p.b,p.a),d=mmPath(a,b,geo.layout);
    return '<path d="'+d+'" fill="none" stroke="'+mmColor(MM_COLORS[p.color%6])+'" stroke-width="'+(p.dim?1.2:2.1)+
      '" stroke-opacity="'+(p.dim?.62:.9)+'" marker-end="url(#mm-arrow-'+(p.color%6)+')"/>';
  }).join('');
  const nodes=geo.nodes.map(n=>mmNodeHTML(n,opts)).join('');
  const host=document.getElementById(cid);if(!host)return;
  host.innerHTML='<div class="mm-stage'+(opts.mini?' mini':'')+'">'+
    '<div class="mm-viewport" style="width:'+(geo.width*scale)+'px;height:'+(geo.height*scale)+'px">'+
    '<div class="mm-graph" style="width:'+geo.width+'px;height:'+geo.height+'px;transform:scale('+scale+')">'+
    '<svg class="mm-links" width="'+geo.width+'" height="'+geo.height+'">'+defs+paths+'</svg>'+nodes+'</div></div></div>'+
    (opts.mini?'':'<div class="mm-legend">'+(model.branches||[]).slice(0,6).map((b,i)=>
      '<span><i style="background:'+mmColor(MM_COLORS[i%6])+'"></i>'+mmEsc(b.icon+' '+b.title)+'</span>').join('')+'</div>');
  _mmRenderCache[cid]={model:model,layout:geo.layout,opts:opts,geo:geo};
  if(!opts.noTarget){_mmTarget=cid;_mmModel=model;}
  return geo;
}
function mmRerender(){
  const c=_mmRenderCache[_mmTarget];if(!c)return;
  mmRender(_mmTarget,c.model,c.layout,Object.assign({},c.opts,{noTarget:true}));
}
function mmToggleBranch(key){_mmExpanded[key]=(_mmExpanded[key]===false);mmRerender();}
function mmExpandAll(open){
  const c=_mmRenderCache[_mmTarget];if(!c)return;
  (c.model.branches||[]).forEach(b=>{_mmExpanded[(c.opts.stateKey||c.model.eventId||'mm')+'|'+b.id]=open;});
  mmRerender();
}
function mmSetLayout(layout){
  _mmLayout=layout;
  try{localStorage.setItem('nv_mm_layout',layout);}catch(e){}
  document.querySelectorAll('.mm-layout-btn').forEach(b=>b.classList.toggle('active',b.dataset.layout===layout));
  if(location.pathname==='/share'){try{history.replaceState(null,'',location.pathname+'?layout='+layout);}catch(e){}}
  const c=_mmRenderCache[_mmTarget];
  if(c)mmRender(_mmTarget,c.model,layout,Object.assign({},c.opts,{noTarget:true}));
}
function mmZoom(delta){
  _mmScale=Math.max(.5,Math.min(1.6,Math.round((_mmScale+delta)*10)/10));mmRerender();
}
/* ---------- exports ---------- */
function mmWrapChars(s,max){const a=[];for(let i=0;i<s.length;i+=max)a.push(s.slice(i,i+max));return a.slice(0,2);}
function mmBuildSVG(){
  const c=_mmRenderCache[_mmTarget];if(!c)return '';
  const g=c.geo,W=g.width+40,H=g.height+40;
  let out='<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">'+
    '<rect width="'+W+'" height="'+H+'" fill="'+mmColor('var(--surface-0)')+'"/>';
  g.paths.forEach(p=>{
    const a=mmEdge(p.a,p.b),b=mmEdge(p.b,p.a);
    out+='<path d="'+mmPath(a,b,g.layout)+'" fill="none" stroke="'+mmColor(MM_COLORS[p.color%6])+
      '" stroke-width="'+(p.dim?1.2:2.1)+'" stroke-opacity="'+(p.dim?.62:.9)+'"/>';
  });
  g.nodes.forEach(n=>{
    const x=n.cx-n.w/2+20,y=n.cy-n.h/2+20,col=mmColor(MM_COLORS[n.color%6]);
    const fill=n.kind==='root'?mmColor('var(--accent)'):mmColor('var(--card)');
    const text=n.kind==='root'?mmColor('var(--on-accent)'):mmColor('var(--text)');
    out+='<rect x="'+x+'" y="'+y+'" width="'+n.w+'" height="'+n.h+'" rx="10" fill="'+fill+
      '" stroke="'+col+'" stroke-width="1.5"/>';
    const title=String(n.data.title||''),max=Math.floor((n.w-20)/12);
    mmWrapChars(title,max).forEach((line,i)=>{
      out+='<text x="'+(x+10)+'" y="'+(y+21+i*15)+'" font-size="12" font-weight="700" fill="'+text+'">'+mmEsc(line)+'</text>';
    });
    if(n.data.sub||n.data.meta)
      out+='<text x="'+(x+10)+'" y="'+(y+n.h-9)+'" font-size="10" fill="'+
        (n.kind==='root'?text:mmColor('var(--muted)'))+'">'+mmEsc(String(n.data.sub||n.data.meta).slice(0,28))+'</text>';
  });
  return out+'</svg>';
}
function mmDownload(kind){
  const svg=mmBuildSVG();if(!svg){alert('请先打开一张脑图');return;}
  const blob=new Blob([svg],{type:'image/svg+xml;charset=utf-8'}),url=URL.createObjectURL(blob);
  const name='newsverify-mindmap-'+(Date.now()/1000|0);
  const a=document.createElement('a');a.href=url;a.download=name+'.svg';a.click();
  if(kind==='png'){
    const img=new Image();
    img.onload=function(){
      const cv=document.createElement('canvas');cv.width=img.width*2;cv.height=img.height*2;
      const ctx=cv.getContext('2d');ctx.scale(2,2);ctx.drawImage(img,0,0);
      const pa=document.createElement('a');pa.href=cv.toDataURL('image/png');pa.download=name+'.png';pa.click();
      URL.revokeObjectURL(url);
    };
    img.onerror=function(){URL.revokeObjectURL(url);};
    img.src=url;
  }else setTimeout(()=>URL.revokeObjectURL(url),4000);
}
/* ---------- sharing ---------- */
function mmCopyText(t){
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).catch(()=>mmCopyFallback(t));}
  else mmCopyFallback(t);
}
function mmCopyFallback(t){
  const ta=document.createElement('textarea');ta.value=t;ta.style.position='fixed';ta.style.opacity='0';
  document.body.appendChild(ta);ta.select();try{document.execCommand('copy');}catch(e){}ta.remove();
}
function mmCloseShare(){const b=document.getElementById('mmShareBg');if(b)b.remove();}
async function mmShare(){
  const c=_mmRenderCache[_mmTarget];if(!c){alert('请先打开一张脑图');return;}
  const box=document.createElement('div');box.id='mmShareBg';box.className='mm-share-bg';
  box.innerHTML='<div class="mm-share-box" onclick="event.stopPropagation()">'+
    '<h3>🔗 分享这张脑图</h3>'+
    '<div class="sub">任何拿到链接的人都能查看这张脑图的静态快照，无需登录。</div>'+
    '<input id="mmShareUrl" readonly value="生成中…" />'+
    '<div class="mm-share-row">'+
      '<button class="btn small" onclick="mmCopyText(document.getElementById(\'mmShareUrl\').value)">复制链接</button>'+
      '<button class="mini-btn" onclick="window.open(document.getElementById(\'mmShareUrl\').value,\'_blank\')">新窗口打开</button>'+
      '<button class="mini-btn" onclick="mmCopyText(JSON.stringify(_mmRenderCache[_mmTarget].model))">复制脑图数据</button>'+
      '<button class="mini-btn" onclick="mmCloseShare()">关闭</button>'+
    '</div><div class="mm-share-qr" id="mmShareQr"></div>'+
    '<div class="mm-share-note">提示：快照包含该新闻的标题、主张、来源与判定摘要，不会暴露后台配置或凭证。可在分享页切换布局、主题并下载 SVG / PNG。</div>'+
    '</div>';
  box.onclick=mmCloseShare;document.body.appendChild(box);
  try{
    const r=await fetch('/api/mindmap/share',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({event_id:c.model.eventId||'',model:c.model,layout:c.layout})});
    const d=await r.json();
    if(!d.url)throw new Error(d.error||'生成失败');
    document.getElementById('mmShareUrl').value=d.url;
    document.getElementById('mmShareQr').innerHTML='<img alt="扫码打开脑图" src="/api/mindmap/share/'+mmEsc(d.token)+'/qrcode" />';
  }catch(e){
    document.getElementById('mmShareUrl').value='生成失败：'+e.message;
  }
}
/* ---------- overview / full mind map modals (console only) ---------- */
async function showMindmap(eventId){
  if(typeof stopDetailPoll==='function')stopDetailPoll();
  _modalView='mindmap';_modalEventId=eventId||null;
  if(eventId)return showEventMindmap(eventId);
  const data=Array.isArray(allEvents)?allEvents:[];
  let html='<h2>🧠 追踪脑图 · 全景 <span class="badge">'+data.length+' 条新闻</span></h2>';
  html+='<div class="sub">每条新闻后面都附有自己的专属脑图。点击卡片进入该新闻的六大维度连线脑图。</div>';
  if(!data.length)html+='<div class="note">暂无任务。提交一条新闻后即可在这里看到全景脑图。</div>';
  else{
    html+='<div class="mm-overview-grid">';
    for(const e of data){
      const st=e.job_status||e.status||'unknown',jr=e.job_result||{},vs=e.verdicts||[],v=vs[0];
      const subs=e.active_subs||0,done=st==='done',run=(st==='running'||st==='queued');
      const badge=subs?'<span class="mm-badge b-track">追踪中</span>':(done?'<span class="mm-badge b-done">已完成</span>':(run?'<span class="mm-badge b-active">进行中</span>':''));
      html+='<div class="mm-ov-card" onclick="showMindmap(\''+mmEsc(e.id)+'\')">'+
        '<div class="ov-t">'+mmEsc(String(e.title||'').slice(0,46))+'</div>'+
        '<div class="ov-m">'+(v?mmEsc(v.label)+' · ':'')+'主张 '+((e.claims||[]).length)+' · 媒体 '+(jr.media_hits||0)+'/30 '+badge+'</div>'+
        '<div class="mm-progress"><i style="width:'+(done?100:(run?45:0))+'%"></i></div></div>';
    }
    html+='</div>';
  }
  document.getElementById('modalContent').innerHTML=html;
  document.getElementById('modalBg').style.display='flex';
}
function mmToolbar(id,readonly){
  const sel=['tree','waterfall','radial'];
  const names={tree:'🌳 树形',waterfall:'💧 瀑布',radial:'✳ 放射'};
  let h='<div class="mm-toolbar"><span style="font-size:11px;color:var(--muted)">布局</span>';
  sel.forEach(l=>{h+='<button class="mini-btn mm-layout-btn'+(l===_mmLayout?' active':'')+'" data-layout="'+l+'" onclick="mmSetLayout(\''+l+'\')">'+names[l]+'</button>';});
  h+='<span class="mm-sep"></span>';
  if(!readonly){
    h+='<button class="mini-btn" onclick="mmExpandAll(true)">⊞ 展开</button>'+
       '<button class="mini-btn" onclick="mmExpandAll(false)">⊟ 收起</button>'+
       '<button class="mini-btn" onclick="mmZoom(-.1)">－</button>'+
       '<button class="mini-btn" onclick="mmZoom(.1)">＋</button><span class="mm-sep"></span>'+
       '<button class="mini-btn" onclick="mmShare()">🔗 分享</button>'+
       '<button class="mini-btn" onclick="mmDownload(\'svg\')">⬇ SVG</button>'+
       '<button class="mini-btn" onclick="mmDownload(\'png\')">⬇ PNG</button><span class="mm-sep"></span>';
  }else{
    h+='<button class="mini-btn" onclick="mmDownload(\'svg\')">⬇ SVG</button>'+
       '<button class="mini-btn" onclick="mmDownload(\'png\')">⬇ PNG</button><span class="mm-sep"></span>';
  }
  return h;
}
async function showEventMindmap(id){
  let d;try{const r=await fetch('/api/events/'+id);d=await r.json();}catch(e){}
  if(!d||!d.id){alert('事件不存在');return;}
  if(_modalView!=='mindmap')return;
  const model=mmModelFromDetail(d);
  let html='<h2>🧠 核查链路脑图 <span class="badge">'+mmEsc(String(id).slice(0,8))+'</span></h2>';
  html+='<div class="sub">'+mmEsc(d.title)+'</div>';
  html+=mmToolbar(id,false);
  html+='<button class="mini-btn" onclick="showMindmap()">← 全景</button>'+
        '<button class="mini-btn" onclick="showDetail(\''+mmEsc(id)+'\')">📄 事件详情</button>';
  html+='<div id="mm-modal-canvas"></div>';
  html+='<div class="mm-hint">💡 连线表示核查链路：中心新闻 → 六大维度 → 具体主张/来源/记录。点击分支节点可展开或收起；不同颜色对应不同维度。</div>';
  document.getElementById('modalContent').innerHTML=html;
  document.getElementById('modalBg').style.display='flex';
  mmRender('mm-modal-canvas',model,_mmLayout,{stateKey:id,context:'modal'});
}
/* Embed the per-news mind map inside the detail modal. */
function mmRenderInlineDetail(d){
  const host=document.getElementById('mm-inline-canvas');if(!host)return;
  const model=mmModelFromDetail(d);
  mmRender('mm-inline-canvas',model,_mmLayout,{stateKey:d.id||'inline',context:'inline',noTarget:true});
  _mmTarget='mm-inline-canvas';_mmModel=model;
}
/* Mini map shown directly behind every news card. */
function mmRenderMinis(){
  (Array.isArray(allEvents)?allEvents:[]).forEach(e=>{
    const host=document.getElementById('mmmini-'+e.id);if(!host)return;
    mmRender('mmmini-'+e.id,mmModelFromList(e),'tree',{mini:true,stateKey:'mini-'+e.id,noTarget:true,readonly:true});
  });
}
/* ---------- public share page ---------- */
const SHARE_THEMES={
  aurora:{'--bg':'#08101f','--card':'#111c33','--surface-0':'#08101f','--surface-1':'#111c33','--text':'#e6edf7','--muted':'#8b9bb5','--border':'#1e2d4d','--accent':'#38bdf8','--accent2':'#818cf8','--accent3':'#34d399','--ok-text':'#4ade80','--bad-text':'#f87171','--accent-soft':'#7dd3fc','--accent2-soft':'#a5b4fc','--on-accent':'#08101f','--shadow':'0 14px 40px rgba(0,0,0,.38)'},
  paper:{'--bg':'#f4f7fc','--card':'#ffffff','--surface-0':'#f8fafd','--surface-1':'#ffffff','--text':'#18253a','--muted':'#5f6f85','--border':'#d3dce9','--accent':'#2563eb','--accent2':'#4f46e5','--accent3':'#0d9488','--ok-text':'#15803d','--bad-text':'#be123c','--accent-soft':'#1d4ed8','--accent2-soft':'#4338ca','--on-accent':'#ffffff','--shadow':'0 12px 34px rgba(30,58,95,.10)'},
  terminal:{'--bg':'#050e09','--card':'#0a1a11','--surface-0':'#050e09','--surface-1':'#0a1a11','--text':'#dcffe9','--muted':'#86af96','--border':'#225236','--accent':'#4ade80','--accent2':'#a3e635','--accent3':'#2dd4bf','--ok-text':'#86efac','--bad-text':'#f87171','--accent-soft':'#86efac','--accent2-soft':'#bef264','--on-accent':'#050e09','--shadow':'0 16px 42px rgba(0,0,0,.55)'}
};
function mmShareTheme(key){
  const t=SHARE_THEMES[key]||SHARE_THEMES.aurora;
  Object.keys(t).forEach(k=>document.documentElement.style.setProperty(k,t[k]));
  const sel=document.getElementById('shareTheme');if(sel)sel.value=key;
  try{localStorage.setItem('nv_share_theme',key);}catch(e){}
}
function mmRenderShare(){
  const s=window.__MM_SHARE__||{};
  const q=new URLSearchParams(location.search).get('layout');
  _mmLayout=(q||s.layout||'tree');
  let key='aurora';try{key=localStorage.getItem('nv_share_theme')||'aurora';}catch(e){}
  mmShareTheme(key);
  const t=document.getElementById('shareTitle');if(t)t.textContent=s.model&&s.model.root?s.model.root.title.replace(/<[^>]+>/g,''):'新闻核查脑图';
  const sub=document.getElementById('shareSub');if(sub)sub.textContent='NewsVerify 公开快照 · 生成于 '+(s.created_at||'—')+' · 可切换布局与主题';
  mmRender('shareCanvas',s.model||{root:{title:'空脑图'},branches:[]},_mmLayout,{stateKey:'share',readonly:true,context:'share'});
  document.querySelectorAll('.mm-layout-btn').forEach(b=>b.classList.toggle('active',b.dataset.layout===_mmLayout));
}
"""

SHARE_THEME_VARS = """
:root{color-scheme:dark}
body{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  background:radial-gradient(900px 420px at 50% -10%,var(--accent2) 0%,transparent 65%),var(--bg);color:var(--text)}
a{color:var(--accent);text-decoration:none}
"""


def share_page(snapshot: dict, token: str, created_at: str) -> str:
    """Build the public, read-only mind-map page for a share token."""
    payload = json.dumps(
        {"model": snapshot.get("model") or {}, "layout": snapshot.get("layout") or "tree",
         "created_at": created_at},
        ensure_ascii=False,
    ).replace("<", "\\u003c").replace("&", "\\u0026")
    toolbar = (
        '<div class="mm-toolbar"><span style="font-size:11px;color:var(--muted)">布局</span>'
        '<button class="mini-btn mm-layout-btn" data-layout="tree" onclick="mmSetLayout(\'tree\')">🌳 树形</button>'
        '<button class="mini-btn mm-layout-btn" data-layout="waterfall" onclick="mmSetLayout(\'waterfall\')">💧 瀑布</button>'
        '<button class="mini-btn mm-layout-btn" data-layout="radial" onclick="mmSetLayout(\'radial\')">✳ 放射</button>'
        '<span class="mm-sep"></span>'
        '<button class="mini-btn" onclick="mmDownload(\'svg\')">⬇ SVG</button>'
        '<button class="mini-btn" onclick="mmDownload(\'png\')">⬇ PNG</button>'
        '<span class="mm-sep"></span><label class="mm-sep" style="font-size:11px;color:var(--muted)">主题</label>'
        '<select id="shareTheme" onchange="mmShareTheme(this.value)" '
        'style="background:var(--surface-1);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:5px 8px;font-size:11px">'
        '<option value="aurora">极光</option><option value="paper">纸张</option><option value="terminal">终端</option></select>'
        '</div>'
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>脑图分享 · NewsVerify</title>
<style>{SHARE_THEME_VARS}
*{{box-sizing:border-box;margin:0;padding:0}}
.mini-btn{{background:var(--surface-1);border:1px solid var(--border);color:var(--text);border-radius:8px;
  padding:5px 10px;font-size:11px;cursor:pointer}}
.mini-btn:hover{{border-color:var(--accent)}}
.mm-sep{{display:inline-block}}
{CSS}</style></head><body>
<div class="share-shell">
  <header><div><h1 id="shareTitle">新闻核查脑图</h1><div class="sub" id="shareSub"></div></div>
    <a href="/theory" title="了解事实核查理论">核查理论 ↗</a></header>
  {toolbar}
  <div id="shareCanvas"></div>
  <div class="mm-hint">此页面是分享时生成的静态快照，内容不会随原任务后续更新而变化。</div>
</div>
<script>{JS}
window.__MM_SHARE__={payload};
window.addEventListener('DOMContentLoaded',mmRenderShare);
</script></body></html>"""
