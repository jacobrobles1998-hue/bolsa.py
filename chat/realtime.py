import json
import streamlit.components.v1 as components


def render_realtime_chat(
    *,
    token: str,
    rol: str,
    cliente_id: int,
    profesional_id: int,
    height: int = 640,
    backend_url: str = "http://127.0.0.1:8000",
):
    token = (token or "").strip()
    rol = (rol or "").strip().lower()
    if rol not in {"cliente", "profesional"}:
        components.html("<div>Rol inválido para chat.</div>", height=80)
        return
    if not token:
        components.html("<div>Sesión inválida (token vacío).</div>", height=80)
        return

    payload = {
        "backend_url": backend_url.rstrip("/"),
        "token": token,
        "rol": rol,
        "cliente_id": int(cliente_id),
        "profesional_id": int(profesional_id),
    }

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
  <style>
    :root {{
      --bg: #ffffff;
      --muted: #64748b;
      --ink: #0f172a;
      --me: #0ea5a4;
      --them: #e2e8f0;
      --border: rgba(15,23,42,.08);
    }}
    body {{
      margin: 0; padding: 0; background: transparent; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial;
      color: var(--ink);
    }}
    .wrap {{
      max-width: 860px;
      margin: 0 auto;
      border: 1px solid var(--border);
      border-radius: 18px;
      overflow: hidden;
      background: rgba(255,255,255,0.92);
      box-shadow: 0 16px 40px rgba(15,23,42,.08);
    }}
    .top {{
      display:flex; align-items:center; justify-content:space-between;
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      background: #f8fafc;
    }}
    .title {{
      font-weight: 800;
      letter-spacing: .2px;
    }}
    .status {{
      font-size: 12px;
      color: var(--muted);
    }}
    .msgs {{
      height: 420px;
      overflow: auto;
      padding: 12px 14px;
      background: var(--bg);
      display:flex;
      flex-direction:column;
      gap: 10px;
    }}
    .row {{
      display:flex;
    }}
    .bubble {{
      max-width: 78%;
      padding: 10px 12px;
      border-radius: 14px;
      font-size: 14px;
      line-height: 1.25;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .me {{
      justify-content: flex-end;
    }}
    .me .bubble {{
      background: rgba(14,165,164,.14);
      border: 1px solid rgba(14,165,164,.22);
    }}
    .them {{
      justify-content: flex-start;
    }}
    .them .bubble {{
      background: var(--them);
      border: 1px solid rgba(15,23,42,.06);
    }}
    .meta {{
      margin-top: 6px;
      font-size: 11px;
      color: var(--muted);
    }}
    .composer {{
      display:flex;
      gap: 10px;
      padding: 12px 14px;
      border-top: 1px solid var(--border);
      background: #ffffff;
    }}
    textarea {{
      flex:1;
      resize:none;
      border-radius: 14px;
      padding: 10px 12px;
      border: 1px solid var(--border);
      outline: none;
      font-size: 14px;
    }}
    button {{
      background: #0ea5a4;
      border: 0;
      color: #fff;
      border-radius: 14px;
      padding: 10px 14px;
      font-weight: 800;
      cursor: pointer;
    }}
    button:disabled {{
      opacity: .6;
      cursor: not-allowed;
    }}
    .hint {{
      padding: 10px 14px;
      font-size: 12px;
      color: var(--muted);
      border-top: 1px dashed rgba(15,23,42,.10);
      background: #fff;
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <div class="title">Chat</div>
      <div class="status" id="status">Conectando…</div>
    </div>

    <div class="msgs" id="msgs"></div>

    <div class="composer">
      <textarea id="txt" rows="2" placeholder="Escribe tu mensaje…"></textarea>
      <button id="send">Enviar</button>
    </div>

    <div class="hint" id="hint" style="display:none;"></div>
  </div>

<script>
  const CFG = {json.dumps(payload)};
  const msgsEl = document.getElementById("msgs");
  const statusEl = document.getElementById("status");
  const hintEl = document.getElementById("hint");
  const txtEl = document.getElementById("txt");
  const sendBtn = document.getElementById("send");

  function setHint(t) {{
    if (!t) {{
      hintEl.style.display = "none";
      hintEl.textContent = "";
      return;
    }}
    hintEl.style.display = "block";
    hintEl.textContent = t;
  }}

  function fmt(ts) {{
    if (!ts) return "";
    return (ts || "").replace("T", " ").slice(0, 19);
  }}

  function scrollBottom() {{
    msgsEl.scrollTop = msgsEl.scrollHeight;
  }}

  function addMsg(m) {{
    const senderRol = (m.sender_rol || "").toLowerCase();
    const senderId = parseInt(m.sender_id || "0", 10);
    const isMe =
      (CFG.rol === "cliente" && senderRol === "cliente" && senderId === CFG.cliente_id) ||
      (CFG.rol === "profesional" && senderRol === "profesional" && senderId === CFG.profesional_id);

    const row = document.createElement("div");
    row.className = "row " + (isMe ? "me" : "them");

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = m.texto || "";

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = fmt(m.created_at);

    const box = document.createElement("div");
    box.appendChild(bubble);
    box.appendChild(meta);

    row.appendChild(box);
    msgsEl.appendChild(row);
  }}

  function renderHistory(items) {{
    msgsEl.innerHTML = "";
    (items || []).forEach(addMsg);
    scrollBottom();
  }}

  function buildSendPayload(texto) {{
    if (CFG.rol === "cliente") {{
      return {{ profesional_id: CFG.profesional_id, texto }};
    }}
    return {{ cliente_id: CFG.cliente_id, texto }};
  }}

  const socket = io(CFG.backend_url, {{
    transports: ["websocket"],
    auth: {{ token: CFG.token }},
  }});

  socket.on("connect", () => {{
    statusEl.textContent = "Conectado";
    setHint("");
    socket.emit("join_conversation", {{
      cliente_id: CFG.cliente_id,
      profesional_id: CFG.profesional_id,
      limit: 120
    }});
  }});

  socket.on("connect_error", (err) => {{
    statusEl.textContent = "Sin conexión";
    setHint("No se pudo conectar al chat. Verifica que el backend esté corriendo en " + CFG.backend_url);
  }});

  socket.on("history", (data) => {{
    if (!data) return;
    if (parseInt(data.cliente_id, 10) !== CFG.cliente_id) return;
    if (parseInt(data.profesional_id, 10) !== CFG.profesional_id) return;
    renderHistory(data.items || []);
  }});

  socket.on("message", (m) => {{
    if (!m) return;
    if (parseInt(m.cliente_id, 10) !== CFG.cliente_id) return;
    if (parseInt(m.profesional_id, 10) !== CFG.profesional_id) return;
    addMsg(m);
    scrollBottom();
  }});

  function sendNow() {{
    const texto = (txtEl.value || "").trim();
    if (!texto) return;
    sendBtn.disabled = true;
    socket.emit("send_message", buildSendPayload(texto));
    txtEl.value = "";
    sendBtn.disabled = false;
    txtEl.focus();
  }}

  sendBtn.addEventListener("click", () => sendNow());
  txtEl.addEventListener("keydown", (e) => {{
    if (e.key === "Enter" && !e.shiftKey) {{
      e.preventDefault();
      sendNow();
    }}
  }});
</script>
</body>
</html>
"""
    components.html(html, height=int(height), scrolling=False)


def render_nav_badge_listener(
    *,
    token: str,
    backend_url: str = "http://localhost:8001",
    interval_ms: int = 1500,
):
    token = (token or "").strip()
    if not token:
        return

    payload = {
        "backend_url": backend_url.rstrip("/"),
        "token": token,
        "interval_ms": int(interval_ms),
    }

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <style>
    body{{margin:0;padding:0;background:transparent;}}
  </style>
</head>
<body>
<script>
  const CFG = {json.dumps(payload)};

  function ensureBadge(btn) {{
    if (!btn) return null;
    btn.style.position = btn.style.position || 'relative';
    let b = btn.querySelector('[data-axon-badge="mensajes"]');
    if (!b) {{
      b = document.createElement('span');
      b.setAttribute('data-axon-badge', 'mensajes');
      b.style.position = 'absolute';
      b.style.top = '-6px';
      b.style.right = '-6px';
      b.style.minWidth = '20px';
      b.style.height = '20px';
      b.style.padding = '0 6px';
      b.style.borderRadius = '999px';
      b.style.display = 'none';
      b.style.alignItems = 'center';
      b.style.justifyContent = 'center';
      b.style.fontSize = '12px';
      b.style.fontWeight = '800';
      b.style.color = '#fff';
      b.style.background = '#ef4444';
      b.style.boxShadow = '0 10px 20px rgba(239,68,68,.25)';
      b.style.border = '2px solid #F0F2F5';
      btn.appendChild(b);
    }}
    return b;
  }}

  function findMensajesButton() {{
    try {{
      const d = window.parent?.document || document;
      const host = d.querySelector('.st-key-nav_p_mensajes');
      const btn = host ? host.querySelector('button') : null;
      return btn;
    }} catch (e) {{
      return null;
    }}
  }}

  async function fetchUnread() {{
    const url = CFG.backend_url + '/unread_count?token=' + encodeURIComponent(CFG.token);
    const r = await fetch(url, {{ method: 'GET' }});
    if (!r.ok) return null;
    return await r.json();
  }}

  let last = null;

  async function tick() {{
    const btn = findMensajesButton();
    if (!btn) return;
    const badge = ensureBadge(btn);
    if (!badge) return;

    const data = await fetchUnread();
    if (!data) return;

    const n = parseInt(data.unread || 0, 10);
    if (last === n) return;
    last = n;

    if (n > 0) {{
      badge.textContent = String(n);
      badge.style.display = 'inline-flex';
    }} else {{
      badge.textContent = '';
      badge.style.display = 'none';
    }}
  }}

  tick();
  setInterval(() => {{ tick(); }}, CFG.interval_ms);
</script>
</body>
</html>
"""
    components.html(html, height=1, scrolling=False)


def render_button_badge_listener(
    *,
    token: str,
    button_key: str,
    backend_url: str = "http://localhost:8001",
    interval_ms: int = 1500,
):
    token = (token or "").strip()
    if not token:
        return

    button_key = (button_key or "").strip()
    if not button_key:
        return

    payload = {
        "backend_url": backend_url.rstrip("/"),
        "token": token,
        "button_key": button_key,
        "interval_ms": int(interval_ms),
    }

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <style>body{{margin:0;padding:0;background:transparent;}}</style>
</head>
<body>
<script>
  const CFG = {json.dumps(payload)};

  function ensureBadge(btn) {{
    if (!btn) return null;
    btn.style.position = btn.style.position || 'relative';
    let b = btn.querySelector('[data-axon-badge="generic"]');
    if (!b) {{
      b = document.createElement('span');
      b.setAttribute('data-axon-badge', 'generic');
      b.style.position = 'absolute';
      b.style.top = '-6px';
      b.style.right = '-6px';
      b.style.minWidth = '20px';
      b.style.height = '20px';
      b.style.padding = '0 6px';
      b.style.borderRadius = '999px';
      b.style.display = 'none';
      b.style.alignItems = 'center';
      b.style.justifyContent = 'center';
      b.style.fontSize = '12px';
      b.style.fontWeight = '800';
      b.style.color = '#fff';
      b.style.background = '#ef4444';
      b.style.boxShadow = '0 10px 20px rgba(239,68,68,.25)';
      b.style.border = '2px solid #F0F2F5';
      btn.appendChild(b);
    }}
    return b;
  }}

  function findButton() {{
    try {{
      const d = window.parent?.document || document;
      const host = d.querySelector('.st-key-' + CSS.escape(CFG.button_key));
      return host ? host.querySelector('button') : null;
    }} catch (e) {{
      return null;
    }}
  }}

  async function fetchUnread() {{
    const url = CFG.backend_url + '/unread_count?token=' + encodeURIComponent(CFG.token);
    const r = await fetch(url, {{ method: 'GET' }});
    if (!r.ok) return null;
    return await r.json();
  }}

  let last = null;

  async function tick() {{
    const btn = findButton();
    if (!btn) return;
    const badge = ensureBadge(btn);
    if (!badge) return;

    const data = await fetchUnread();
    if (!data) return;

    const n = parseInt(data.unread || 0, 10);
    if (last === n) return;
    last = n;

    if (n > 0) {{
      badge.textContent = String(n);
      badge.style.display = 'inline-flex';
    }} else {{
      badge.textContent = '';
      badge.style.display = 'none';
    }}
  }}

  tick();
  setInterval(() => {{ tick(); }}, CFG.interval_ms);
</script>
</body>
</html>
"""
    components.html(html, height=1, scrolling=False)


def render_tab_badge_listener(
    *,
    token: str,
    tab_text: str,
    backend_url: str = "http://localhost:8001",
    interval_ms: int = 1500,
):
    token = (token or "").strip()
    tab_text = (tab_text or "").strip()
    if not token or not tab_text:
        return

    payload = {
        "backend_url": backend_url.rstrip("/"),
        "token": token,
        "tab_text": tab_text,
        "interval_ms": int(interval_ms),
    }

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <style>body{{margin:0;padding:0;background:transparent;}}</style>
</head>
<body>
<script>
  const CFG = {json.dumps(payload)};

  function ensureBadge(el) {{
    if (!el) return null;
    el.style.position = el.style.position || 'relative';
    let b = el.querySelector('[data-axon-badge="tab"]');
    if (!b) {{
      b = document.createElement('span');
      b.setAttribute('data-axon-badge', 'tab');
      b.style.position = 'absolute';
      b.style.top = '-6px';
      b.style.right = '-6px';
      b.style.minWidth = '20px';
      b.style.height = '20px';
      b.style.padding = '0 6px';
      b.style.borderRadius = '999px';
      b.style.display = 'none';
      b.style.alignItems = 'center';
      b.style.justifyContent = 'center';
      b.style.fontSize = '12px';
      b.style.fontWeight = '800';
      b.style.color = '#fff';
      b.style.background = '#ef4444';
      b.style.boxShadow = '0 10px 20px rgba(239,68,68,.25)';
      b.style.border = '2px solid #F0F2F5';
      el.appendChild(b);
    }}
    return b;
  }}

  function findTab() {{
    try {{
      const d = window.parent?.document || document;
      const tabs = d.querySelectorAll('div[data-testid="stTabs"] [data-baseweb="tab"]');
      for (const t of tabs) {{
        const txt = (t.textContent || '').trim();
        if (!txt) continue;
        if (txt === CFG.tab_text || txt.startsWith(CFG.tab_text)) return t;
      }}
      return null;
    }} catch (e) {{
      return null;
    }}
  }}

  async function fetchUnread() {{
    const url = CFG.backend_url + '/unread_count?token=' + encodeURIComponent(CFG.token);
    const r = await fetch(url, {{ method: 'GET' }});
    if (!r.ok) return null;
    return await r.json();
  }}

  let last = null;

  async function tick() {{
    const tab = findTab();
    if (!tab) return;
    const badge = ensureBadge(tab);
    if (!badge) return;

    const data = await fetchUnread();
    if (!data) return;

    const n = parseInt(data.unread || 0, 10);
    if (last === n) return;
    last = n;

    if (n > 0) {{
      badge.textContent = String(n);
      badge.style.display = 'inline-flex';
    }} else {{
      badge.textContent = '';
      badge.style.display = 'none';
    }}
  }}

  tick();
  setInterval(() => {{ tick(); }}, CFG.interval_ms);
</script>
</body>
</html>
"""
    components.html(html, height=1, scrolling=False)


def render_inbox_listener(
    *,
    token: str,
    rol: str,
    user_id: int,
    backend_url: str = "http://localhost:8001",
    disable_reload: bool = False,
):
    token = (token or "").strip()
    rol = (rol or "").strip().lower()
    if rol not in {"cliente", "profesional"}:
        return
    if not token:
        return

    payload = {
        "backend_url": backend_url.rstrip("/"),
        "token": token,
        "rol": rol,
        "user_id": int(user_id),
        "disable_reload": bool(disable_reload),
    }

    html = f"""
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <script src=\"https://cdn.socket.io/4.7.5/socket.io.min.js\"></script>
  <style>body{{margin:0;padding:0;background:transparent;}}</style>
</head>
<body>
<script>
  const CFG = {json.dumps(payload)};
  let pending = false;

  const socket = io(CFG.backend_url, {{
    transports: [\"websocket\"],
    auth: {{ token: CFG.token }},
  }});

  socket.on("inbox_ping", (m) => {{
    if (CFG.disable_reload) return;
    if (pending) return;
    if (!m) return;

    const cid = parseInt(m.cliente_id || \"0\", 10);
    const pid = parseInt(m.profesional_id || \"0\", 10);

    if (CFG.rol === \"cliente\") {{
      if (cid !== parseInt(CFG.user_id, 10)) return;
    }} else {{
      if (pid !== parseInt(CFG.user_id, 10)) return;
    }}

    pending = true;
    setTimeout(() => {{
      try {{
        window.parent.location.reload();
      }} catch (e) {{
        window.location.reload();
      }}
    }}, 150);
  }});
</script>
</body>
</html>
"""
    components.html(html, height=1, scrolling=False)