from pathlib import Path
p=Path(r'xmfls-osm-model\src\style.css'); s=p.read_text(encoding='utf-8')
extra=r'''
.copy-pose{pointer-events:auto;display:block;margin:6px 0 1px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.06);color:#e7c49d;border-radius:4px;padding:4px 6px;font:7px/1.2 var(--mono);cursor:pointer;letter-spacing:.02em}
.copy-pose:hover{background:rgba(255,255,255,.13);color:#fff}
#toast{position:fixed;left:50%;bottom:78px;transform:translateX(-50%);z-index:40;background:rgba(39,51,42,.94);color:#f4efe3;border-radius:6px;padding:7px 13px;font:8px/1.4 var(--mono);opacity:0;pointer-events:none;transition:opacity .18s;max-width:70vw;text-align:center}
#toast.show{opacity:1}
body.walking #bottom .help{color:var(--accent)}
body.walking .view-btn[data-view="walk"]{background:var(--accent);color:#fff;border-color:var(--accent)}
'''
if extra not in s:
    s=s.replace('/* ---------- responsive ---------- */', extra+'\n/* ---------- responsive ---------- */')
p.write_text(s,encoding='utf-8'); print('css added')
