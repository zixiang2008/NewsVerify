"""Login, registration and admin sign-in pages (NVDS design system)."""

from __future__ import annotations

from app.web.design import page_shell

_ERRORS = {
    "bad": "用户名或 PIN 码不正确，请重试。",
    "taken": "该用户名已被注册，请换一个。",
    "invite": "邀请码无效、已过期或次数已用完。",
    "invalid": "输入格式有误，请检查后重试。",
    "ok": "注册成功，请使用用户名与 PIN 登录。",
    "created": "账号已创建，请登录。",
}


def _auth_shell(version: str, head: str, form: str, foot: str, note: str = "") -> str:
    notice = ""
    if note and note in _ERRORS:
        cls = "ok" if note in ("ok", "created") else "bad"
        notice = f'<div class="nvds-alert {cls}">{_ERRORS[note]}</div>'
    body = f"""
<div class="nvds-auth">
  <div class="nvds-auth-card nvds-card nvds-rise">
    <div class="nvds-auth-head">
      <div class="nvds-auth-logo">NV</div>
      <div class="nvds-kicker">NEWSVERIFY · EVIDENCE WORKSPACE</div>
      <h1>{head}</h1>
      <p>自建、可审计的新闻事实核查与持续追踪工作台</p>
    </div>
    {notice}
    {form}
    <div class="nvds-sep">安全提示</div>
    <div class="nvds-hint" style="text-align:center">账号 + 4 位 PIN 登录 · 邀请码注册 · 凭证仅保存在你的自托管服务中</div>
    <div class="nvds-auth-foot">{foot}</div>
  </div>
</div>
<div style="position:fixed;bottom:14px;left:0;right:0;text-align:center;color:var(--muted);font-size:10px">NewsVerify v{version} · 本地优先 · 证据可追溯</div>
"""
    return page_shell(f"{head} · NewsVerify", body)


def login_page(version: str, note: str = "") -> str:
    form = """
<form method="post" action="/login" autocomplete="on">
  <div class="nvds-field">
    <label class="nvds-label" for="u">用户名</label>
    <input class="nvds-input" id="u" name="username" placeholder="请输入用户名" maxlength="32" autocomplete="username" autofocus required />
  </div>
  <div class="nvds-field">
    <label class="nvds-label" for="p">PIN 码 <span>4 位数字</span></label>
    <input class="nvds-input center" id="p" name="pin" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" placeholder="••••" autocomplete="current-password" required />
  </div>
  <button class="nvds-btn block" type="submit">进入控制台 →</button>
</form>
"""
    foot = '还没有账号？<a href="/register">使用邀请码注册</a> · <a href="/admin/login">管理员入口</a>'
    return _auth_shell(version, "欢迎回来", form, foot, note)


def register_page(version: str, prefill: str = "", note: str = "") -> str:
    form = f"""
<form method="post" action="/register" autocomplete="off">
  <div class="nvds-field">
    <label class="nvds-label" for="u">用户名 <span>2–32 位</span></label>
    <input class="nvds-input" id="u" name="username" placeholder="字母、数字、下划线或汉字" maxlength="32" required />
  </div>
  <div class="nvds-field">
    <label class="nvds-label" for="p">设置 PIN 码 <span>4 位数字</span></label>
    <input class="nvds-input center" id="p" name="pin" type="password" inputmode="numeric" pattern="[0-9]{{4}}" maxlength="4" placeholder="••••" required />
  </div>
  <div class="nvds-field">
    <label class="nvds-label" for="c">邀请码 <span>6 位数字</span></label>
    <input class="nvds-input center" id="c" name="code" inputmode="numeric" pattern="[0-9]{{6}}" maxlength="6" placeholder="••••••" value="{prefill}" required />
    <div class="nvds-hint">邀请码由超级管理员生成并分享，每个码有独立的使用次数与有效期。</div>
  </div>
  <button class="nvds-btn block" type="submit">创建账号 →</button>
</form>
"""
    foot = '已有账号？<a href="/login">返回登录</a>'
    return _auth_shell(version, "创建账号", form, foot, note)


def admin_login_page(version: str, note: str = "") -> str:
    form = """
<form method="post" action="/admin/login" autocomplete="on">
  <div class="nvds-field">
    <label class="nvds-label" for="u">管理员账号</label>
    <input class="nvds-input" id="u" name="username" placeholder="caishen / kayla" maxlength="32" autocomplete="username" autofocus required />
  </div>
  <div class="nvds-field">
    <label class="nvds-label" for="p">PIN 码 <span>4 位数字</span></label>
    <input class="nvds-input center" id="p" name="pin" type="password" inputmode="numeric" pattern="[0-9]{4}" maxlength="4" placeholder="••••" autocomplete="current-password" required />
  </div>
  <button class="nvds-btn block" type="submit">进入管理后台 →</button>
</form>
<div class="nvds-alert" style="font-size:11px">仅超级管理员可进入。内置管理员：caishen / kayla（初始 PIN 分别为 1314 / 0720）。</div>
"""
    foot = '<a href="/login">← 返回普通登录</a>'
    return _auth_shell(version, "管理后台登录", form, foot, note)
