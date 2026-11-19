"""Super-admin console pages: overview and account / invitation management."""

from __future__ import annotations

from app.web.design import page_shell, tabs_html


def _nav(active: str) -> str:
    return tabs_html(active)


def _top(title: str, subtitle: str, active: str) -> str:
    return f"""
<div class="nvds-shell">
  <div class="nvds-top">
    <div>
      <div class="nvds-crumb"><a href="/">控制台</a> / <a href="/admin">后台管理</a> / {title}</div>
      <div class="nvds-kicker">NEWSVERIFY · SUPER ADMIN</div>
      <div class="nvds-title" style="margin-top:4px">{title}</div>
      <div class="nvds-sub">{subtitle}</div>
    </div>
    <div class="nvds-flex">
      <span class="nvds-chip mute" id="whoami" style="display:none"></span>
      <button class="nvds-btn ghost sm" onclick="location.href='/logout'">退出登录</button>
    </div>
  </div>
  {_nav(active)}
"""


OVERVIEW_JS = r"""
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function loadCfg(){const d=await(await fetch('/api/admin/config')).json();
const rows=[['LLM 主地址',d.llm_base_url],['LLM 备用地址',d.llm_base_url_fallback],['核查模型',d.llm_model],['判定模型',d.llm_judge_model],
['LLM API Key',d.llm_api_key_masked],['搜索提供方',d.search_provider],['SearXNG 地址',d.searxng_base_url],['Brave Key',d.brave_key_masked],
['Google FactCheck Key',d.google_factcheck_key_masked],['Public API Key',d.api_key_masked],['Telegram Bot',d.telegram_bot_configured?'已配置':'未配置'],
['允许的用户 ID',d.telegram_allowed_user_ids],['自定义 RSS 源',d.custom_feed_urls],['版本',d.version]];
document.getElementById('cfgTable').innerHTML=rows.map(r=>`<tr><td class="k">${esc(r[0])}</td><td class="nvds-code">${esc(r[1])||'—'}</td></tr>`).join('');
document.getElementById('envNotice').textContent=d.env_notice;}
async function loadChannels(){const d=await(await fetch('/api/admin/channels')).json();
document.getElementById('chTable').innerHTML='<tr><th>平台</th><th>状态</th><th>文档 / 入口</th></tr>'+d.channels.map(c=>
`<tr><td>${esc(c.label)}</td><td><span class="nvds-chip ${c.configured?'ok':'mute'}">${c.configured?'已配置':'待配置'}</span></td><td><a href="${esc(c.docs)}" target="_blank">${esc(c.docs)}</a><br><span class="nvds-code">/api/v1/im/${esc(c.key)}/webhook</span></td></tr>`).join('');
document.getElementById('testCh').innerHTML=d.channels.map(c=>`<option value="${esc(c.key)}">${esc(c.label)}</option>`).join('');}
async function testChannel(){const key=document.getElementById('testCh').value,chat=document.getElementById('testChat').value;
const r=await fetch('/api/admin/channels/'+key+'/test',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chat_id:chat,text:'NewsVerify 后台测试消息'})});const d=await r.json();
document.getElementById('testResult').textContent=d.ok?'发送成功':'未配置或发送失败（'+JSON.stringify(d)+'）';}
loadCfg();loadChannels();
"""


def overview_page(version: str) -> str:
    body = _top("后台总览", "查看 API 配置、账号体系与即时通讯接入入口", "overview") + f"""
<div class="nvds-grid2 nvds-rise d1">
  <div class="nvds-card nvds-card-pad">
    <div class="nvds-panel-head"><h2>🔑 调用的 API 与可设置信息</h2><span class="nvds-chip mute">v{version}</span></div>
    <div class="nvds-scroll"><table class="nvds-table" id="cfgTable"><tr><td>加载中…</td></tr></table></div>
    <div class="nvds-hint" id="envNotice" style="margin-top:10px"></div>
  </div>
  <div class="nvds-card nvds-card-pad">
    <div class="nvds-panel-head"><h2>🚀 快速入口</h2></div>
    <div class="nvds-steps">
      <div class="nvds-step"><span class="num">1</span><b>账号与邀请码</b><span>创建注册码、查看用户、一键复制分享链接。</span></div>
      <div class="nvds-step"><span class="num">2</span><b>API 管理与调试</b><span>创建管理 Key、查看全部接口、生成 Agent 接入代码。</span></div>
      <div class="nvds-step"><span class="num">3</span><b>IM 接入向导</b><span>扫码或 Token 辅助接入 11 个主流平台。</span></div>
      <div class="nvds-step"><span class="num">4</span><b>系统运行状况</b><span>返回控制台查看实时探测与主备 API 状态。</span></div>
    </div>
    <div class="nvds-btn-row" style="margin-top:16px">
      <button class="nvds-btn sm" onclick="location.href='/admin/accounts'">管理账号 →</button>
      <button class="nvds-btn soft sm" onclick="location.href='/admin/api'">API 控制台 →</button>
      <button class="nvds-btn ghost sm" onclick="location.href='/'">返回控制台</button>
    </div>
  </div>
</div>

<div class="nvds-card nvds-card-pad nvds-rise d2" style="margin-top:16px">
  <div class="nvds-panel-head"><h2>💬 即时通讯接入入口（主流平台）</h2>
    <button class="nvds-btn soft sm" onclick="location.href='/admin/im'">打开 IM 接入向导 →</button></div>
  <div class="nvds-alert">统一 Webhook 入口：<span class="nvds-code">/api/v1/im/&#123;平台key&#125;/webhook</span>。下方为已保存平台的只读概览。</div>
  <div class="nvds-scroll"><table class="nvds-table" id="chTable"><tr><td>加载中…</td></tr></table></div>
</div>

<div class="nvds-card nvds-card-pad nvds-rise d3" style="margin-top:16px">
  <div class="nvds-panel-head"><h2>📡 Webhook 接入测试</h2><span class="nvds-hint">向指定平台通道发送一条测试回执</span></div>
  <div class="nvds-flex">
    <select class="nvds-select" id="testCh" style="max-width:220px"></select>
    <input class="nvds-input" id="testChat" placeholder="chat_id" value="test" style="max-width:180px" />
    <button class="nvds-btn sm" onclick="testChannel()">发送测试</button>
    <span class="nvds-hint" id="testResult"></span>
  </div>
</div>
</div>"""
    return page_shell("后台总览 · NewsVerify", body, extra_js=OVERVIEW_JS)


ACCOUNTS_JS = r"""
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function loadAccounts(){const d=await(await fetch('/api/admin/users')).json();
  document.getElementById('userTable').innerHTML='<tr><th>用户名</th><th>显示名</th><th>类别</th><th>状态</th><th>注册来源</th><th>最近登录</th></tr>'+
   d.users.map(u=>`<tr><td><b>${esc(u.username)}</b></td><td>${esc(u.display_name)}</td><td><span class="nvds-chip ${u.role==='super_admin'?'':'mute'}">${u.role==='super_admin'?'超级管理员':'普通用户'}</span></td>
   <td><span class="nvds-status ${u.active?'on':'off'}"></span>${u.active?'启用':'停用'}</td><td>${esc(u.invited_by||'内置')}</td><td>${esc(u.last_login_at||'—')}</td></tr>`).join('');
  const inv=await(await fetch('/api/admin/invites')).json();
  document.getElementById('inviteTable').innerHTML='<tr><th>邀请码</th><th>类别</th><th>使用</th><th>有效期</th><th>备注</th><th>操作</th></tr>'+
   inv.invites.map(v=>`<tr><td class="nvds-code" style="font-size:15px;font-weight:800">${esc(v.code)}</td><td><span class="nvds-chip mute">${v.role==='super_admin'?'超级管理员':'普通用户'}</span></td>
   <td>${v.used_count}/${v.max_uses}</td><td>${esc(v.expires_at||'长期有效')}</td><td>${esc(v.note||'—')}</td>
   <td>${v.active?`<button class="nvds-copy" onclick="revokeInvite('${esc(v.code)}')">撤销</button>`:'已撤销'}</td></tr>`).join('');
}
async function genInvites(){const btn=document.getElementById('genBtn');btn.disabled=true;btn.textContent='生成中…';
  const body={count:parseInt(document.getElementById('iCount').value||'1',10),role:document.getElementById('iRole').value,
    note:document.getElementById('iNote').value,max_uses:parseInt(document.getElementById('iUses').value||'1',10),
    expires_days:parseInt(document.getElementById('iDays').value||'0',10)||null};
  const r=await fetch('/api/admin/invites/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  const d=await r.json();btn.disabled=false;btn.textContent='生成邀请码';
  if(!d.ok){nvToast(d.detail||'生成失败');return;}
  const box=document.getElementById('inviteResult');box.style.display='block';
  document.getElementById('inviteCards').innerHTML=d.codes.map(c=>`<div class="nvds-card nvds-card-pad" style="padding:14px">
     <div class="nvds-flex" style="justify-content:space-between"><span class="nvds-code" style="font-size:20px;font-weight:850">${esc(c.code)}</span>
     <button class="nvds-copy" data-copy="${esc(c.share_text)}">复制邀请说明</button></div>
     <a class="nvds-hint" href="${esc(c.url)}" target="_blank">${esc(c.url)}</a></div>`).join('');
  document.getElementById('inviteBatchCopy').setAttribute('data-copy',d.codes.map(c=>c.share_text).join('\n\n'));
  nvCopyEls('#inviteResult .nvds-copy, #inviteBatchCopy');loadAccounts();
}
async function revokeInvite(code){const r=await(await fetch('/api/admin/invites/'+code,{method:'DELETE'})).json();nvToast(r.ok?'已撤销':'撤销失败');loadAccounts();}
loadAccounts();
"""


def accounts_page(version: str) -> str:
    body = _top("账号与邀请码", "管理用户、生成六位邀请码并一键复制带地址的分享说明", "accounts") + f"""
<div class="nvds-card nvds-card-pad nvds-rise d1">
  <div class="nvds-panel-head"><h2>🎟️ 生成邀请码</h2><span class="nvds-chip">仅超级管理员可操作</span></div>
  <div class="nvds-grid3">
    <div class="nvds-field"><label class="nvds-label">生成数量 <span>1–200</span></label><input class="nvds-input" id="iCount" type="number" min="1" max="200" value="5" /></div>
    <div class="nvds-field"><label class="nvds-label">注册后类别</label><select class="nvds-select" id="iRole"><option value="user">普通用户</option><option value="super_admin">超级管理员</option></select></div>
    <div class="nvds-field"><label class="nvds-label">每个码可用次数</label><input class="nvds-input" id="iUses" type="number" min="1" max="100" value="1" /></div>
    <div class="nvds-field"><label class="nvds-label">有效期（天，0 为长期）</label><input class="nvds-input" id="iDays" type="number" min="0" max="3650" value="30" /></div>
    <div class="nvds-field" style="grid-column:span 2"><label class="nvds-label">备注</label><input class="nvds-input" id="iNote" placeholder="例如：团队 A 批量邀请" /></div>
  </div>
  <div class="nvds-btn-row"><button class="nvds-btn" id="genBtn" onclick="genInvites()">生成邀请码</button>
    <button class="nvds-copy" id="inviteBatchCopy" data-copy="" style="padding:10px 14px">复制全部邀请说明</button></div>
  <div class="nvds-hint" style="margin-top:8px">生成后可逐个复制「邀请说明」——包含注册地址、邀请码与使用提示，直接发给对方即可。</div>
  <div id="inviteResult" style="display:none;margin-top:16px">
    <div class="nvds-divider"></div><div class="nvds-kicker" style="margin-bottom:10px">本批次新生成的邀请码</div>
    <div class="nvds-grid2" id="inviteCards"></div>
  </div>
</div>

<div class="nvds-card nvds-card-pad nvds-rise d2" style="margin-top:16px">
  <div class="nvds-panel-head"><h2>👥 用户列表</h2><span class="nvds-hint">内置超级管理员：caishen / kayla</span></div>
  <div class="nvds-scroll"><table class="nvds-table" id="userTable"><tr><td>加载中…</td></tr></table></div>
</div>

<div class="nvds-card nvds-card-pad nvds-rise d3" style="margin-top:16px">
  <div class="nvds-panel-head"><h2>🎫 邀请码列表</h2><span class="nvds-hint">撤销后立即失效</span></div>
  <div class="nvds-scroll"><table class="nvds-table" id="inviteTable"><tr><td>加载中…</td></tr></table></div>
</div>
</div>"""
    return page_shell("账号与邀请码 · NewsVerify", body, extra_js=ACCOUNTS_JS)
