from pathlib import Path
p=Path(r'xmfls-osm-model\src\index.html'); s=p.read_text(encoding='utf-8')
# ellipse axes fields after height row
old='''      <div class="edit-row"><label id="edHLabel">高度</label><button class="nudge" data-field="h" data-dir="-1">−</button><input id="edH" type="number" step="0.5"><button class="nudge" data-field="h" data-dir="1">+</button><span id="edHUnit">m</span></div>
      <div class="edit-tip" id="editHeightNote">该建筑单独高度（米）；不影响其他建筑。</div>'''
new='''      <div class="edit-row"><label id="edHLabel">高度</label><button class="nudge" data-field="h" data-dir="-1">−</button><input id="edH" type="number" step="0.5"><button class="nudge" data-field="h" data-dir="1">+</button><span id="edHUnit">m</span></div>
      <div id="ellipseFields" hidden>
        <div class="edit-row"><label>长轴</label><button class="nudge" data-field="a" data-dir="-1">−</button><input id="edA" type="number" step="1"><button class="nudge" data-field="a" data-dir="1">+</button><span>m</span></div>
        <div class="edit-row"><label>短轴</label><button class="nudge" data-field="b" data-dir="-1">−</button><input id="edB" type="number" step="1"><button class="nudge" data-field="b" data-dir="1">+</button><span>m</span></div>
      </div>
      <div class="edit-tip" id="editHeightNote">该建筑单独高度（米）；不影响其他建筑。</div>'''
if old not in s: raise SystemExit('height row missing')
s=s.replace(old,new)
# walk button
s=s.replace('<button class="view-btn" data-view="auto" id="autoBtn">自动旋转</button>',
            '<button class="view-btn" data-view="auto" id="autoBtn">自动旋转</button>\n    <button class="view-btn" data-view="walk" id="walkBtn">第一人称</button>')
# copy button inside coords HUD
s=s.replace('<div class="coord-note">X→东 · Z→南 · 角度自北顺时针 · 原点 24.457256, 118.031006</div>',
            '<button id="copyPose" class="copy-pose">复制坐标 / 角度</button>\n  <div class="coord-note">X→东 · Z→南 · 角度自北顺时针 · 原点 24.457256, 118.031006</div>')
# toast before loader
s=s.replace('<div id="loader">','<div id="toast" role="status"></div>\n<div id="loader">')
p.write_text(s,encoding='utf-8')
c=Path(r'xmfls-osm-model\src\style.css'); css=c.read_text(encoding='utf-8')
extra=r'''
.copy-pose{pointer-events:auto;display:block;margin:6px 0 1px;border:1px solid rgba(255,255,255,.18);background:rgba(255,255,255,.06);color:#e7c49d;border-radius:4px;padding:4px 6px;font:7px/1.2 var(--mono);cursor:pointer;letter-spacing:.02em}
.copy-pose:hover{background:rgba(255,255,255,.13);color:#fff}
#toast{position:fixed;left:50%;bottom:78px;transform:translateX(-50%);z-index:40;background:rgba(39,51,42,.94);color:#f4efe3;border-radius:6px;padding:7px 13px;font:8px/1.4 var(--mono);opacity:0;pointer-events:none;transition:opacity .18s;max-width:70vw;text-align:center}
#toast.show{opacity:1}
body.walking #bottom .help{color:var(--accent)}
body.walking .view-btn[data-view="walk"]{background:var(--accent);color:#fff;border-color:var(--accent)}
'''
c=c.replace('/* ---------- responsive ---------- */', extra+'\n/* ---------- responsive ---------- */')
c.write_text(c,encoding='utf-8')
print('UI for axes/walk/copy added')
