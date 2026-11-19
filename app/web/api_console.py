"""Super-admin API console: key management, settings, docs and live debugger."""

from __future__ import annotations

import json

from app.web.design import page_shell, tabs_html

ENDPOINTS = [
    {"method": "GET", "path": "/api/v1/status", "name": "服务状态与计数", "desc": "返回任务/事件/追踪数量与版本，用于连通性检查。", "params": []},
    {"method": "GET", "path": "/api/v1/version", "name": "版本与主题", "desc": "版本号、代号、9 套主题与历史发布记录。", "params": []},
    {"method": "GET", "path": "/api/v1/top-media", "name": "Top30 媒体榜", "desc": "30 家公信力媒体、名次与来源说明。", "params": []},
    {"method": "GET", "path": "/api/v1/source-policy", "name": "可信来源白名单", "desc": "媒体、核查机构、搜索引擎与权威机构白名单。", "params": []},
    {"method": "POST", "path": "/api/v1/check", "name": "提交新闻核查", "desc": "异步入队一条核查任务，返回 event_id 与 job_id。", "params": [
        {"name": "text", "where": "body", "required": True, "desc": "新闻文字或链接"},
        {"name": "mode", "where": "body", "required": False, "desc": "full / top30 / method"},
        {"name": "freq", "where": "body", "required": False, "desc": "none / 6h / 24h / week"}]},
    {"method": "GET", "path": "/api/v1/query/news", "name": "查询新闻", "desc": "按标题或 ID 搜索事件，可筛选状态。", "params": [
        {"name": "q", "where": "query", "required": False, "desc": "标题或事件 ID 关键字"},
        {"name": "status", "where": "query", "required": False, "desc": "queued/active/done/failed"},
        {"name": "limit", "where": "query", "required": False, "desc": "返回条数，默认 20"}]},
    {"method": "GET", "path": "/api/v1/events", "name": "事件列表", "desc": "最近 50 条事件及最新判定摘要。", "params": []},
    {"method": "GET", "path": "/api/v1/events/{event_id}", "name": "事件详情", "desc": "主张、判定、证据来源与媒体覆盖。", "params": [
        {"name": "event_id", "where": "path", "required": True, "desc": "事件 ID"}]},
    {"method": "GET", "path": "/api/v1/events/{event_id}/process", "name": "全过程资料", "desc": "审计级完整记录：每一步进度、主张、判定、证据、追踪通知、任务历史。", "params": [
        {"name": "event_id", "where": "path", "required": True, "desc": "事件 ID"}]},
    {"method": "GET", "path": "/api/v1/events/{event_id}/mindmap", "name": "脑图模型", "desc": "返回可直接交给前端脑图渲染器的六分支模型 JSON。", "params": [
        {"name": "event_id", "where": "path", "required": True, "desc": "事件 ID"},
        {"name": "layout", "where": "query", "required": False, "desc": "tree / waterfall / radial"}]},
    {"method": "GET", "path": "/api/v1/jobs/{job_id}", "name": "任务详情", "desc": "查看单个任务的状态、载荷、进度与错误。", "params": [
        {"name": "job_id", "where": "path", "required": True, "desc": "任务 ID"}]},
    {"method": "POST", "path": "/api/v1/track/{event_id}", "name": "开启/更新追踪", "desc": "按 6h/24h/week 持续追踪事件变化，幂等。", "params": [
        {"name": "event_id", "where": "path", "required": True, "desc": "事件 ID"},
        {"name": "interval", "where": "body", "required": False, "desc": "6h / 24h / week"}]},
    {"method": "POST", "path": "/api/v1/untrack/{event_id}", "name": "停止追踪", "desc": "关闭该事件的所有订阅。", "params": [
        {"name": "event_id", "where": "path", "required": True, "desc": "事件 ID"}]},
    {"method": "DELETE", "path": "/api/v1/events/{event_id}", "name": "删除事件", "desc": "连带删除主张、证据、判定与订阅。", "params": [
        {"name": "event_id", "where": "path", "required": True, "desc": "事件 ID"}]},
    {"method": "GET", "path": "/api/v1/keys/me", "name": "当前 Key 信息", "desc": "校验 Key 有效性并回显名称与权限范围。", "params": []},
]

AGENT_PROMPT = """你是 NewsVerify 接入助手。服务地址 BASE_URL，凭证 KEY。
1) 先 GET /api/v1/keys/me 验证凭证；
2) 用户给出新闻文本时 POST /api/v1/check 提交，保存 event_id；
3) 轮询 GET /api/v1/jobs/{job_id} 直到 status=done/failed；
4) 用 GET /api/v1/events/{event_id}/process 取全部证据与判定；
5) 需要可视化时 GET /api/v1/events/{event_id}/mindmap 取脑图模型；
6) 所有请求头必须携带 X-API-Key: KEY；写操作需要 write 权限。
回答时注明每条结论对应的证据 URL，不得臆造来源。"""

API_JS = r"""
const ENDPOINTS = __ENDPOINTS__;
const AGENT_PROMPT = __AGENT_PROMPT__;
let currentEp = ENDPOINTS[0];
const $ = id => document.getElementById(id);
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function methodChip(m){return '<span class="nvds-chip '+(m==='GET'?'ok':(m==='DELETE'?'bad':'warn'))+'">'+m+'</span>';}

function renderEndpoints(filter){
  const q=(filter||'').toLowerCase();
  $('epList').innerHTML=ENDPOINTS.filter(e=>(e.path+e.name+e.desc).toLowerCase().includes(q)).map((e,i)=>
   `<div class="nvds-step" style="cursor:pointer;margin-bottom:8px;border-color:${e===currentEp?'var(--accent)':'var(--border)'}" onclick="pickEp(${ENDPOINTS.indexOf(e)})">
     <div class="nvds-flex" style="justify-content:space-between">${methodChip(e.method)}<span class="nvds-code" style="font-size:11px">${esc(e.path)}</span></div>
     <b style="margin-top:6px">${esc(e.name)}</b><span>${esc(e.desc)}</span></div>`).join('');
}
function pickEp(i){currentEp=ENDPOINTS[i];renderEndpoints($('epFilter').value);renderEpDetail();renderSamples();}
function renderEpDetail(){
  const e=currentEp;
  $('epDetail').innerHTML=`<div class="nvds-flex" style="justify-content:space-between">${methodChip(e.method)}<span class="nvds-chip mute">${e.params.length} 个参数</span></div>
   <div class="nvds-title" style="margin:8px 0 4px;font-size:17px">${esc(e.name)}</div><div class="nvds-sub">${esc(e.desc)}</div>
   <div class="nvds-codebox"><div class="nvds-cap">路径</div><pre>${esc(e.path)}</pre></div>
   ${e.params.length?`<div class="nvds-divider"></div><div class="nvds-kicker" style="margin-bottom:8px">参数</div>
   <table class="nvds-table"><tr><th>名称</th><th>位置</th><th>必填</th><th>说明</th></tr>${e.params.map(p=>
   `<tr><td class="nvds-code">${esc(p.name)}</td><td>${esc(p.where)}</td><td>${p.required?'<span class="nvds-chip bad">是</span>':'<span class="nvds-chip mute">否</span>'}</td><td>${esc(p.desc)}</td></tr>`).join('')}</table>`:''}`;
  $('paramBox').innerHTML=e.params.map(p=>`<div class="nvds-field"><label class="nvds-label">${esc(p.name)} <span>${esc(p.where)}${p.required?' · 必填':''}</span></label>
    <input class="nvds-input" data-pname="${esc(p.name)}" data-pwhere="${esc(p.where)}" placeholder="${esc(p.desc)}" /></div>`).join('');
  $('bodyBox').style.display=['POST','PUT','PATCH'].includes(e.method)?'block':'none';
}
function reqUrl(){
  let path=currentEp.path;
  const params={};
  document.querySelectorAll('#paramBox input').forEach(i=>{const v=i.value.trim();if(v)params[i.dataset.pname]=v;});
  path=path.replace(/\{(\w+)\}/g,(m,k)=>encodeURIComponent(params[k]||'< '+k+' >'));
  const q=Object.entries(params).filter(([k])=>!currentEp.path.includes('{'+k+'}')).map(([k,v])=>encodeURIComponent(k)+'='+encodeURIComponent(v)).join('&');
  return ($('baseUrl').value||location.origin).replace(/\/$/,'')+path+(q?'?'+q:'');
}
function samples(){
  const key=$('testKey').value||'YOUR_KEY', url=reqUrl();
  const body=currentEp.method==='GET'||currentEp.method==='DELETE'?'':($('bodyJson').value||'{}');
  const curl=`curl -X ${currentEp.method} "${url}" \\\n  -H "X-API-Key: ${key}"${body?` \\\n  -H "Content-Type: application/json" \\\n  -d '${body}'`:''}`;
  const py=`import requests\n\nurl = "${url}"\nheaders = {"X-API-Key": "${key}"}\n`+
    (body?`payload = ${body}\nr = requests.${currentEp.method.toLowerCase()}(url, headers=headers, json=payload, timeout=30)\n`
        :`r = requests.${currentEp.method.toLowerCase()}(url, headers=headers, timeout=30)\n`)+
    `print(r.status_code)\nprint(r.json())`;
  const js=`const r = await fetch(${JSON.stringify(url)}, {\n  method: ${JSON.stringify(currentEp.method)},\n  headers: { "X-API-Key": ${JSON.stringify(key)}${body?', "Content-Type": "application/json"':''} }${body?`,\n  body: ${JSON.stringify(body)}`:''}\n});\nconst data = await r.json();\nconsole.log(data);`;
  return {curl,py,js};
}
function renderSamples(){const s=samples();
  $('codeCurl').textContent=s.curl;$('codePy').textContent=s.py;$('codeJs').textContent=s.js;
  $('codePrompt').textContent=AGENT_PROMPT.replaceAll('BASE_URL',($('baseUrl').value||location.origin).replace(/\/$/,''))+'\\n\\n示例凭证：'+($('testKey').value||'YOUR_KEY');
}
async function runRequest(){const btn=$('runBtn');btn.disabled=true;btn.textContent='请求中…';
  const key=$('testKey').value.trim();if(!key){nvToast('请先填写 API Key');btn.disabled=false;btn.textContent='发送请求';return;}
  const opts={method:currentEp.method,headers:{'X-API-Key':key}};
  if(!['GET','DELETE'].includes(currentEp.method)){opts.headers['Content-Type']='application/json';opts.body=$('bodyJson').value||'{}';}
  try{const r=await fetch(reqUrl(),opts);const text=await r.text();let pretty=text;try{pretty=JSON.stringify(JSON.parse(text),null,2)}catch(e){}
    $('respBox').textContent='HTTP '+r.status+'\\n\\n'+pretty;
  }catch(e){$('respBox').textContent='请求失败：'+e.message;}
  btn.disabled=false;btn.textContent='发送请求';
}

async function loadKeys(){const d=await(await fetch('/api/admin/api-keys')).json();
  $('keyTable').innerHTML='<tr><th>名称</th><th>Key</th><th>权限</th><th>状态</th><th>调用</th><th>最近使用</th><th>操作</th></tr>'+
   d.keys.map(k=>`<tr><td>${esc(k.name)}</td><td class="nvds-code">${esc(k.key)}</td><td>${k.scopes.map(s=>`<span class="nvds-chip mute">${esc(s)}</span>`).join(' ')}</td>
   <td><span class="nvds-status ${k.enabled?'on':'off'}"></span>${k.enabled?'启用':'停用'}</td><td>${k.calls}</td><td>${esc(k.last_used_at||'—')}</td>
   <td class="nvds-flex"><button class="nvds-copy" data-copy="${esc(k.key)}">复制</button>
   <button class="nvds-copy" onclick="toggleKey('${esc(k.key)}',${!k.enabled})">${k.enabled?'停用':'启用'}</button>
   <button class="nvds-copy" onclick="delKey('${esc(k.key)}')">删除</button></td></tr>`).join('');
  if(!$('testKey').value&&d.keys.length)$('testKey').value=d.keys[0].key;
  renderSamples();
}
async function createKey(){const body={name:$('kName').value||'新 Key',scopes:Array.from(document.querySelectorAll('input[name=kScope]:checked')).map(x=>x.value)};
  const d=await(await fetch('/api/admin/api-keys',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})).json();
  if(!d.ok){nvToast(d.detail||'创建失败');return;}
  $('newKeyBox').style.display='block';$('newKeyVal').textContent=d.key;
  document.querySelectorAll('#newKeyBox [data-copy]').forEach(b=>b.setAttribute('data-copy',d.key));
  $('testKey').value=d.key;nvCopyEls('#newKeyBox .nvds-copy');loadKeys();
}
async function toggleKey(key,enabled){await fetch('/api/admin/api-keys/'+encodeURIComponent(key),{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled})});loadKeys();}
async function delKey(key){if(!confirm('确认删除该 Key？使用它的 Agent 将立即失效。'))return;await fetch('/api/admin/api-keys/'+encodeURIComponent(key),{method:'DELETE'});loadKeys();}
async function loadSettings(){const d=await(await fetch('/api/admin/api/settings')).json();const s=d.settings;
  $('setApiEnabled').checked=!!s.api_enabled;$('setAllowWrite').checked=!!s.allow_write;
  $('setMaxResults').value=s.max_results;$('setRate').value=s.rate_limit_per_min;
  $('setBase').value=s.public_base_url||location.origin;$('setNote').value=s.agent_note||'';renderSamples();}
async function saveSettings(){const body={api_enabled:$('setApiEnabled').checked,allow_write:$('setAllowWrite').checked,
  max_results:parseInt($('setMaxResults').value,10),rate_limit_per_min:parseInt($('setRate').value,10),
  public_base_url:$('setBase').value.trim(),agent_note:$('setNote').value};
  const r=await fetch('/api/admin/api/settings',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  nvToast(r.ok?'设置已保存':'保存失败');renderSamples();}
renderEndpoints('');renderEpDetail();renderSamples();loadKeys();loadSettings();
"""


def _codebox(cap: str, sid: str) -> str:
    return f"""<div class="nvds-codebox"><div class="nvds-cap">{cap}</div>
<button class="nvds-copy nvds-copy" data-copy-target="{sid}">复制</button>
<pre id="{sid}"></pre></div>"""


def api_console_page(version: str) -> str:
    endpoint_json = json.dumps(ENDPOINTS, ensure_ascii=False)
    prompt_json = json.dumps(AGENT_PROMPT, ensure_ascii=False)
    js = API_JS.replace("__ENDPOINTS__", endpoint_json).replace("__AGENT_PROMPT__", prompt_json)
    body = f"""
<div class="nvds-shell">
  <div class="nvds-top">
    <div>
      <div class="nvds-crumb"><a href="/">控制台</a> / <a href="/admin">后台管理</a> / API 管理与调试</div>
      <div class="nvds-kicker">NEWSVERIFY · AGENT API CONSOLE</div>
      <div class="nvds-title" style="margin-top:4px">API 管理与调试控制台</div>
      <div class="nvds-sub">创建管理 Key、设置运行时参数、查阅全部接口，并在此直接调试与生成 Agent 接入代码。</div>
    </div>
    <button class="nvds-btn ghost sm" onclick="location.href='/logout'">退出登录</button>
  </div>
  {tabs_html('api')}

  <div class="nvds-grid2 nvds-rise d1">
    <div class="nvds-card nvds-card-pad">
      <div class="nvds-panel-head"><h2>🔐 管理 Key</h2><span class="nvds-chip">仅超级管理员</span></div>
      <div class="nvds-flex" style="margin-bottom:12px">
        <input class="nvds-input nvds-grow" id="kName" placeholder="Key 名称，例如：research-agent" style="max-width:260px" />
        <label class="nvds-hint"><input type="checkbox" name="kScope" value="read" checked /> read</label>
        <label class="nvds-hint"><input type="checkbox" name="kScope" value="write" /> write</label>
        <label class="nvds-hint"><input type="checkbox" name="kScope" value="admin" /> admin</label>
        <button class="nvds-btn sm" onclick="createKey()">新建 Key</button>
      </div>
      <div class="nvds-alert" id="newKeyBox" style="display:none">新 Key（仅此刻完整显示，请立即复制保存）：
        <div class="nvds-flex" style="margin-top:6px"><code class="nvds-code" id="newKeyVal"></code>
        <button class="nvds-copy" data-copy="">复制 Key</button></div></div>
      <div class="nvds-scroll"><table class="nvds-table" id="keyTable"><tr><td>加载中…</td></tr></table></div>
      <div class="nvds-hint" style="margin-top:10px">read 仅查询；write 允许提交/追踪/删除；admin 保留扩展权限。停用后使用该 Key 的请求立即返回 403。</div>
    </div>

    <div class="nvds-card nvds-card-pad">
      <div class="nvds-panel-head"><h2>⚙️ 运行时设置</h2><button class="nvds-btn sm" onclick="saveSettings()">保存设置</button></div>
      <div class="nvds-grid2">
        <label class="nvds-hint"><input type="checkbox" id="setApiEnabled" /> 启用 API 总开关</label>
        <label class="nvds-hint"><input type="checkbox" id="setAllowWrite" /> 允许写操作</label>
        <div class="nvds-field"><label class="nvds-label">单次查询上限</label><input class="nvds-input" id="setMaxResults" type="number" min="1" max="1000" value="100" /></div>
        <div class="nvds-field"><label class="nvds-label">限速（次/分钟，展示用）</label><input class="nvds-input" id="setRate" type="number" min="1" value="120" /></div>
      </div>
      <div class="nvds-field"><label class="nvds-label">对外基础地址</label><input class="nvds-input" id="setBase" placeholder="https://new.caishen.today" /></div>
      <div class="nvds-field"><label class="nvds-label">Agent 接入提示</label><textarea class="nvds-textarea" id="setNote" style="min-height:70px"></textarea></div>
      <div class="nvds-alert">设置保存在数据库中，重启后依然有效；无需修改 .env 或重启容器。</div>
    </div>
  </div>

  <div class="nvds-card nvds-card-pad nvds-rise d2" style="margin-top:16px">
    <div class="nvds-panel-head"><h2>🧪 在线调试</h2><span class="nvds-hint">选择接口 → 填参数 → 发送，响应直接显示</span></div>
    <div class="nvds-side">
      <div>
        <input class="nvds-input" id="epFilter" placeholder="🔍 筛选接口，例如 process / track" oninput="renderEndpoints(this.value)" style="margin-bottom:10px" />
        <div class="nvds-scroll" style="max-height:430px">div id="epList"></div></div>
        <div id="epDetail" style="margin-top:14px"></div>
      </div>
      <div>
        <div class="nvds-field"><label class="nvds-label">API Key</label><input class="nvds-input" id="testKey" placeholder="nvk_…" /></div>
        <div class="nvds-field"><label class="nvds-label">Base URL</label><input class="nvds-input" id="baseUrl" placeholder="https://new.caishen.today" /></div>
        <div class="nvds-field"><label class="nvds-label">请求参数</label><div id="paramBox"></div></div>
        <div class="nvds-field" id="bodyBox" style="display:none"><label class="nvds-label">JSON Body</label>
          <textarea class="nvds-textarea nvds-mono" id="bodyJson" style="min-height:80px">{{"text":"测试新闻文本","mode":"full","freq":"none"}}</textarea></div>
        <button class="nvds-btn block" id="runBtn" onclick="runRequest()">发送请求 →</button>
        <div class="nvds-codebox" style="margin-top:12px"><div class="nvds-cap">响应</div><pre id="respBox" style="max-height:240px">—</pre></div>
      </div>
    </div>
  </div>

  <div class="nvds-card nvds-card-pad nvds-rise d3" style="margin-top:16px">
    <div class="nvds-panel-head"><h2>🧩 调试代码与 Agent 接入</h2><span class="nvds-hint">代码会随上方 Key、地址与参数实时更新</span></div>
    <div class="nvds-grid2">
      {_codebox('cURL', 'codeCurl')}
      {_codebox('Python · requests', 'codePy')}
      {_codebox('JavaScript · fetch', 'codeJs')}
      <div class="nvds-codebox"><div class="nvds-cap">Agent 系统提示词（可直接复制给其他 Agent）</div>
        <button class="nvds-copy nvds-copy" data-copy-target="codePrompt">复制</button><pre id="codePrompt"></pre></div>
    </div>
    <div class="nvds-divider"></div>
    <div class="nvds-steps">
      <div class="nvds-step"><span class="num">1</span><b>创建 Key</b><span>在上方填写名称并勾选权限，创建后立刻复制保存。</span></div>
      <div class="nvds-step"><span class="num">2</span><b>验证连通</b><span>GET /api/v1/keys/me，返回 200 即凭证有效。</span></div>
      <div class="nvds-step"><span class="num">3</span><b>提交与轮询</b><span>POST /api/v1/check 得到 job_id，轮询任务状态至完成。</span></div>
      <div class="nvds-step"><span class="num">4</span><b>取全过程资料</b><span>GET /api/v1/events/&#123;id&#125;/process 得到证据链与判定。</span></div>
    </div>
    <div class="nvds-alert">所有 <span class="nvds-code">/api/v1/*</span> 接口都必须携带请求头 <span class="nvds-code">X-API-Key</span>；也可使用 <span class="nvds-code">?api_key=</span> 查询参数。完整机器可读规格见 <a href="/openapi.json" target="_blank">/openapi.json</a>。</div>
  </div>
</div>
"""
    # fix a literal placeholder typo introduced for readability
    body = body.replace('div id="epList"', '<div id="epList"')
    extra = js + """
document.querySelectorAll('[data-copy-target]').forEach(function(b){b.addEventListener('click',function(){
  nvCopy(document.getElementById(b.getAttribute('data-copy-target')).textContent,b);});});
"""
    return page_shell("API 管理与调试 · NewsVerify", body, extra_js=extra)
