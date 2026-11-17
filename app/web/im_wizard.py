"""Interactive instant-messaging onboarding console (rendered at /admin).

Reference design: the adapter-driven WebUI wizards of AstrBot / NoneBot /
Koishi. Users connect a platform in four guided steps — obtain credentials,
fill a form, scan a QR / copy the inbound URL, and run a real test — without
editing code or restarting the container.
"""

from __future__ import annotations

import json

from app.version import VERSION

STYLE = """
.IM-wrap{color:var(--text)}
.im-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap;margin-bottom:14px}
.im-sub{color:var(--muted);font-size:12px;line-height:1.7}
.im-badge{display:inline-block;font-size:10px;padding:2px 9px;border-radius:999px;background:#123;color:var(--accent);border:1px solid var(--border)}
.im-toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:12px 0}
.im-toolbar input,.im-toolbar select,.im-field input,.im-field select,.im-field textarea{background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:8px;padding:8px 10px;font-size:12px;font-family:inherit;outline:none}
.im-toolbar input:focus,.im-field input:focus{border-color:var(--accent)}
.im-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(228px,1fr));gap:10px}
.im-card{background:var(--bg);border:1px solid var(--border);border-radius:12px;padding:13px;cursor:pointer;transition:.15s;position:relative}
.im-card:hover{border-color:var(--accent);transform:translateY(-1px)}
.im-card.on{border-color:var(--ok)}
.im-card .im-ic{font-size:20px}
.im-card .im-name{font-weight:700;font-size:13px;margin-top:6px}
.im-card .im-desc{color:var(--muted);font-size:11px;line-height:1.5;margin-top:5px;min-height:33px}
.im-card .im-foot{display:flex;justify-content:space-between;align-items:center;margin-top:9px;font-size:10px}
.im-status{font-size:10px}.im-status.ok{color:var(--ok)}.im-status.no{color:var(--bad)}
.im-panel{display:none;margin-top:14px;border:1px solid var(--border);border-radius:12px;background:var(--bg);overflow:hidden}
.im-panel.show{display:block}
.im-tabs{display:flex;gap:0;border-bottom:1px solid var(--border);background:var(--card)}
.im-tab{padding:10px 14px;font-size:12px;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent}
.im-tab.active{color:var(--accent);border-color:var(--accent);font-weight:700}
.im-body{padding:14px;max-height:520px;overflow:auto}
.im-steps{margin:0 0 12px;padding-left:20px;color:var(--muted);font-size:12px;line-height:1.9}
.im-steps li::marker{color:var(--accent)}
.im-field{margin-bottom:10px}
.im-field label{display:block;font-size:11px;color:var(--muted);margin-bottom:4px}
.im-field input{width:100%;box-sizing:border-box}
.im-field .fh{font-size:10px;color:var(--muted);margin-top:3px;line-height:1.5}
.im-urlbox{display:flex;gap:6px;align-items:center;background:var(--card);border:1px solid var(--border);border-radius:8px;padding:7px 9px;margin:8px 0;font-size:11px;flex-wrap:wrap}
.im-urlbox code{color:var(--accent);word-break:break-all;flex:1;min-width:180px}
.im-actions{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}
.im-btn{padding:7px 12px;border:none;border-radius:8px;background:var(--accent);color:#08101f;font-weight:700;font-size:11px;cursor:pointer}
.im-btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.im-btn.warn{background:transparent;color:var(--bad);border:1px solid var(--bad)}
.im-btn:disabled{opacity:.5;cursor:not-allowed}
.im-result{margin-top:10px;font-size:11px;line-height:1.7;padding:9px;border-radius:8px;background:var(--card);border:1px solid var(--border);white-space:pre-wrap;word-break:break-word}
.im-qr{display:flex;gap:14px;align-items:flex-start;flex-wrap:wrap;margin-top:10px}
.im-qr img{width:168px;height:168px;background:#fff;border-radius:10px;padding:8px;box-sizing:border-box}
.im-qr .qt{font-size:11px;color:var(--muted);line-height:1.8;max-width:330px}
.im-links a{color:var(--accent);font-size:11px;margin-right:12px}
.im-pill{font-size:10px;padding:2px 8px;border-radius:999px;background:#123;border:1px solid var(--border);color:var(--muted)}
"""

JS = r"""
const IM_GUIDES=__GUIDES__;
const IM_CH_CAT=__CATALOGUE__;
let imSelected=null,imCfg=null,imPoll=null;
function escI(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function imModeLabel(m){return m==='qr'?'扫码优先':m==='token'?'Bot Token':'Webhook / 凭证';}
function imOrigin(){return location.protocol+'//'+location.host;}
async function imApi(path,opt){const r=await fetch(path,opt);let d={};try{d=await r.json();}catch(e){}if(!r.ok&&!d.ok)throw new Error(d.error||('HTTP '+r.status));return d;}
async function loadIm(){
  const d=await imApi('/api/admin/channels/guide');
  imCfg=d.config||{};
  const wrap=document.getElementById('imGrid');
  wrap.innerHTML=d.channels.map(c=>{
    const g=c.guide||{},cfg=imCfg[c.key]||{};const on=!!cfg.configured;
    return '<div class="im-card '+(on?'on':'')+'" data-key="'+escI(c.key)+'" onclick="openIm(\''+escI(c.key)+'\')">'+
      '<div class="im-ic">'+escI(g.icon||'💬')+'</div>'+
      '<div class="im-name">'+escI(c.label)+'</div>'+
      '<div class="im-desc">'+escI(g.summary||'')+'</div>'+
      '<div class="im-foot"><span class="im-pill">'+escI(imModeLabel(g.mode))+'</span>'+
      '<span class="im-status '+(on?'ok':'no')+'">'+(on?'● 已对接':'○ 待配置')+'</span></div></div>';
  }).join('');
}
function openIm(key){
  const c=IM_CH_CAT.find(x=>x.key===key),g=IM_GUIDES[key]||{};
  if(!c)return;imSelected=key;clearInterval(imPoll);
  document.querySelectorAll('.im-card').forEach(x=>x.classList.toggle('on',x.dataset.key===key));
  const cfg=(imCfg[key]||{}).credentials||{};
  const fields=(g.fields||[]).map(f=>{
    const val=cfg[f.name]||'';
    const input=f.kind==='textarea'
      ? '<textarea id="f_'+f.name+'" rows="3" placeholder="'+escI(f.placeholder||'')+'">'+escI(val)+'</textarea>'
      : '<input id="f_'+f.name+'" type="'+(f.kind==='password'?'password':(f.kind==='url'?'url':'text'))+'" value="'+escI(val)+'" placeholder="'+escI(f.placeholder||'')+'" />';
    return '<div class="im-field"><label>'+escI(f.label)+(f.required?' *':'')+'</label>'+input+
      (f.help?'<div class="fh">'+escI(f.help)+'</div>':'')+'</div>';
  }).join('');
  const inbound=imOrigin()+'/api/v1/im/'+escI(key)+'/webhook';
  const qr=(g.qr||{});
  const steps=(g.steps||[]).map(s=>'<li>'+escI(s)+'</li>').join('');
  const p=document.getElementById('imPanel');
  p.className='im-panel show';
  p.innerHTML='<div class="im-tabs"><div class="im-tab active" onclick="imTab(0)">① 接入步骤</div>'+
    '<div class="im-tab" onclick="imTab(1)">② 填写凭证</div>'+
    '<div class="im-tab" onclick="imTab(2)">③ 扫码 / 回调</div>'+
    '<div class="im-tab" onclick="imTab(3)">④ 测试与状态</div></div>'+
    '<div class="im-body">'+
    '<div class="im-page" data-p="0"><h3 style="font-size:13px;color:var(--accent)">'+escI(c.label)+' · 接入指引</h3>'+
      '<div class="im-sub" style="margin:6px 0 10px">'+escI(g.summary||'')+'</div><ol class="im-steps">'+steps+'</ol>'+
      '<div class="im-links">'+(g.connect_url?'<a href="'+escI(g.connect_url)+'" target="_blank">↗ 打开官方配置台</a>':'')+
      (g.docs?'<a href="'+escI(g.docs)+'" target="_blank">↗ 官方文档</a>':'')+'</div>'+
      '<div class="im-actions"><button class="im-btn" onclick="imTab(1)">下一步：填写凭证 →</button></div></div>'+
    '<div class="im-page" data-p="1" style="display:none"><div class="im-sub" style="margin-bottom:10px">凭证只保存在本系统数据库，页面回显时自动脱敏；留空表示沿用已保存值。</div>'+
      fields+'<div class="im-actions"><button class="im-btn" onclick="imSave()">保存配置</button>'+
      '<button class="im-btn ghost" onclick="imTab(2)">下一步：扫码 / 回调 →</button></div></div>'+
    '<div class="im-page" data-p="2" style="display:none"><div class="im-sub" style="margin-bottom:8px">本系统的统一接收地址（把它填入平台后台）：</div>'+
      '<div class="im-urlbox"><code>'+inbound+'</code><button class="im-btn ghost" onclick="imCopy(\''+escI(inbound)+'\')">复制</button></div>'+
      (qr.supported||qr.kind==='official'?'<div class="im-qr"><div id="imQrImg"></div><div class="qt">'+escI(qr.hint||'')+'</div></div>'+
      '<div class="im-actions"><button class="im-btn ghost" onclick="imQr()">生成绑定二维码</button>'+
      (qr.kind==='deeplink'?'<button class="im-btn ghost" onclick="imPollStart()">开始等待扫码绑定</button>':'')+'</div>':'<div class="im-sub">'+escI(qr.hint||'')+'</div>')+
      '<div class="im-actions"><button class="im-btn" onclick="imTab(3)">下一步：测试 →</button></div></div>'+
    '<div class="im-page" data-p="3" style="display:none"><div class="im-sub" style="margin-bottom:8px">真实发送一条测试消息到该平台，确认收发链路可用。</div>'+
      '<div class="im-toolbar"><input id="imTestChat" placeholder="chat_id / 用户ID（Telegram 必填）" value="'+escI((imCfg[key]||{}).bound_chat_id||'')+'" />'+
      '<button class="im-btn" onclick="imTest()">发送测试消息</button></div>'+
      '<div id="imResult" class="im-result">尚未测试。</div>'+
      '<div class="im-actions" style="margin-top:14px"><button class="im-btn warn" onclick="imDelete()">清除此平台配置</button></div></div>'+
    '</div>';
}
function imTab(n){
  document.querySelectorAll('.im-tab').forEach((t,i)=>t.classList.toggle('active',i===n));
  document.querySelectorAll('.im-page').forEach(p=>p.style.display=(p.dataset.p==n?'block':'none'));
}
function imCollect(){const g=IM_GUIDES[imSelected]||{};const o={};
  (g.fields||[]).forEach(f=>{const el=document.getElementById('f_'+f.name);if(el)o[f.name]=el.value.trim();});return o;}
async function imSave(){try{
  const d=await imApi('/api/admin/channels/'+imSelected+'/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(imCollect())});
  await loadIm();document.getElementById('imResult')&&(document.getElementById('imResult').textContent='✅ 配置已保存并立即生效，无需重启。');
}catch(e){alert('保存失败：'+e.message);}}
async function imTest(){const box=document.getElementById('imResult');box.textContent='正在发送…';
  try{const chat=document.getElementById('imTestChat').value.trim();
    const d=await imApi('/api/admin/channels/'+imSelected+'/test',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:chat,text:'NewsVerify 接入测试：收到这条消息即表示对接成功。'})});
    box.textContent=d.ok?('✅ 测试消息已发送成功'+(d.detail?' · '+d.detail:'')):('❌ 发送失败：'+(d.detail||'未配置或凭证有误'));
    await loadIm();
  }catch(e){box.textContent='❌ '+e.message;}}
async function imQr(){const box=document.getElementById('imQrImg');box.innerHTML='生成中…';
  try{const d=await imApi('/api/admin/channels/'+imSelected+'/qrcode');
    box.innerHTML=d.svg?('<img alt="绑定二维码" src="data:image/svg+xml;base64,'+btoa(unescape(encodeURIComponent(d.svg)))+'" />'+
      (d.url?'<div class="im-sub" style="margin-top:6px">或打开：<a href="'+escI(d.url)+'" target="_blank">'+escI(d.url)+'</a></div>':'')):escI(d.error||'无法生成二维码');
  }catch(e){box.textContent='生成失败：'+e.message;}}
async function imPollStart(){clearInterval(imPoll);let n=0;
  imPoll=setInterval(async()=>{try{const d=await imApi('/api/admin/channels/'+imSelected+'/bind-status');
    if(d.bound){clearInterval(imPoll);alert('✅ 已检测到绑定：chat_id='+d.bound_chat_id);await loadIm();}
    else if(++n>30){clearInterval(imPoll);alert('等待超时，请确认已扫码并发送 /start。');}
  }catch(e){}},3000);alert('已开始等待扫码，请用手机扫码并向机器人发送 /start。');}
async function imDelete(){if(!confirm('确定清除该平台的配置吗？'))return;
  await imApi('/api/admin/channels/'+imSelected+'/config',{method:'DELETE'});clearInterval(imPoll);await loadIm();
  document.getElementById('imResult').textContent='配置已清除。';}
function imCopy(t){navigator.clipboard&&navigator.clipboard.writeText(t).then(()=>alert('已复制')).catch(()=>prompt('请手动复制：',t));}
loadIm();
"""

HTML = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>NewsVerify IM 接入向导</title>
<style>__STYLE__</style></head><body>
<div class="IM-wrap">
  <div class="im-head"><div><h2 style="font-size:16px;color:var(--accent);margin:0">💬 即时通讯接入向导</h2>
  <div class="im-sub">主流平台一键对接：<span class="im-badge">扫码 / Token 辅助</span> · 填表即生效 · 真实消息测试。参考 AstrBot / NoneBot 适配器生态的向导式配置。</div></div>
  <a href="/admin" style="color:var(--accent);font-size:12px">← 返回后台</a></div>
  <div id="imGrid" class="im-grid"></div>
  <div id="imPanel" class="im-panel"></div>
</div>
<script>__JS__</script></body></html>"""


def render_page(guides: dict, catalogue: list) -> str:
    js = (JS.replace("__GUIDES__", json.dumps(guides, ensure_ascii=False))
            .replace("__CATALOGUE__", json.dumps(catalogue, ensure_ascii=False)))
    return (HTML.replace("__STYLE__", STYLE).replace("__JS__", js)
                .replace("__APP_VERSION__", VERSION))
