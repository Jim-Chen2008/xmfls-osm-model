from pathlib import Path
html = Path(r'xmfls-osm-model\src\index.html')
h = html.read_text(encoding='utf-8')

anchor = '  <section class="panel-block selected-block" id="selectedBlock">'
block = '''  <section class="panel-block edit-block" id="editBlock" hidden>
    <div class="block-head"><span>编辑 / EDIT</span><span id="editModeLabel">选择对象</span></div>
    <p class="edit-tip" id="editEmpty">点击模型里的建筑、球场、大门或椭圆，即可单独改位置与高度。拖动空白处仍是转视角。</p>
    <div id="editForm" hidden>
      <div class="edit-object" id="editName">—</div>
      <div class="edit-row"><label>X</label><button class="nudge" data-field="x" data-dir="-1">−</button><input id="edX" type="number" step="0.5"><button class="nudge" data-field="x" data-dir="1">+</button><span>m</span></div>
      <div class="edit-row"><label>Z</label><button class="nudge" data-field="z" data-dir="-1">−</button><input id="edZ" type="number" step="0.5"><button class="nudge" data-field="z" data-dir="1">+</button><span>m</span></div>
      <div class="edit-row"><label>Y</label><button class="nudge" data-field="y" data-dir="-1">−</button><input id="edY" type="number" step="0.5"><button class="nudge" data-field="y" data-dir="1">+</button><span>m</span></div>
      <div class="edit-row"><label>旋转</label><button class="nudge" data-field="rot" data-dir="-1">−</button><input id="edR" type="number" step="1"><button class="nudge" data-field="rot" data-dir="1">+</button><span>°</span></div>
      <div class="edit-row"><label id="edHLabel">高度</label><button class="nudge" data-field="h" data-dir="-1">−</button><input id="edH" type="number" step="0.5"><button class="nudge" data-field="h" data-dir="1">+</button><span id="edHUnit">m</span></div>
      <div class="edit-tip" id="editHeightNote">建筑高度按米；补全构筑物为高度系数。</div>
      <div class="edit-actions">
        <button id="undoEdit" title="Ctrl+Z">撤销</button>
        <button id="redoEdit" title="Ctrl+Shift+Z">反撤销</button>
        <button id="resetObj">复位选中</button>
        <button id="resetAll">全部复位</button>
      </div>
    </div>
    <div class="edit-actions">
      <button id="exportEdit">导出修改</button>
      <button id="importEdit">导入修改</button>
      <button id="overlayBtn">实景叠图</button>
      <button id="closeEdit">退出编辑</button>
    </div>
    <input id="importFile" type="file" accept=".json,application/json" hidden>
    <div class="edit-status" id="editStatus"></div>
  </section>

'''
if anchor not in h: raise SystemExit('selected block anchor missing')
h = h.replace(anchor, block + anchor)

h = h.replace('    <button class="view-btn" data-view="auto" id="autoBtn">自动旋转</button>\n',
              '    <button class="view-btn" data-view="auto" id="autoBtn">自动旋转</button>\n    <button id="editToggle" class="edit-fab">编辑</button>\n')

modal = '''<div id="overlayModal" class="overlay-modal" hidden>
  <div class="overlay-shell">
    <button id="overlayClose" aria-label="关闭实景叠图">×</button>
    <iframe id="overlayFrame" title="实景叠图 / 坐标校准"></iframe>
  </div>
</div>
'''
if '<div id="loader">' not in h: raise SystemExit('loader missing')
h = h.replace('<div id="loader">', modal + '<div id="loader">')
html.write_text(h, encoding='utf-8')

css = Path(r'xmfls-osm-model\src\style.css')
c = css.read_text(encoding='utf-8')
extra = r'''
/* ---------- object editor ---------- */
.edit-fab{
  border:1px solid rgba(167,84,55,.4); background:rgba(251,247,238,.75); color:var(--accent);
  font:600 9px/1 var(--sans); padding:8px 12px; border-radius:5px; margin-left:4px; cursor:pointer;
}
.edit-fab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.edit-block{border-top:1px solid rgba(167,84,55,.18)}
.edit-tip{font-size:8px;line-height:1.65;color:var(--muted);margin:0 0 7px}
.edit-object{font-size:11px;font-weight:650;color:var(--ink);margin:2px 0 7px;padding-bottom:5px;border-bottom:1px solid rgba(44,55,45,.08)}
.edit-row{display:flex;align-items:center;gap:4px;margin:4px 0}
.edit-row label{flex:0 0 30px;font-size:8px;color:var(--soft)}
.edit-row input{flex:1;min-width:0;width:55px;background:rgba(255,255,255,.7);border:1px solid var(--line);border-radius:4px;padding:4px 5px;font:8px/1.2 var(--mono);color:var(--ink);outline:none}
.edit-row input:focus{border-color:rgba(167,84,55,.7)}
.edit-row>span{flex:0 0 10px;font:7px/1 var(--mono);color:var(--muted)}
.nudge{width:20px;height:22px;padding:0;border:1px solid var(--line);background:rgba(255,255,255,.55);border-radius:3px;font:12px/1 var(--mono);color:var(--soft);cursor:pointer}
.nudge:hover{background:#fff;color:var(--ink)}
.edit-actions{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px}
.edit-actions button{font-size:7.5px;padding:5px 7px}
.edit-status{font:7px/1.5 var(--mono);color:var(--accent);margin-top:5px;min-height:10px}
.edit-block .block-head{color:var(--accent)}
.overlay-modal{position:fixed;inset:0;z-index:60;background:rgba(24,32,27,.62);backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center}
.overlay-modal[hidden]{display:none}
.overlay-shell{position:relative;width:min(94vw,1250px);height:min(92vh,900px);background:#f4efe5;border-radius:10px;overflow:hidden;box-shadow:0 30px 90px -30px rgba(0,0,0,.6)}
.overlay-shell iframe{width:100%;height:100%;border:0;display:block}
#overlayClose{position:absolute;right:10px;top:8px;z-index:2;width:28px;height:28px;border-radius:50%;border:1px solid var(--line);background:rgba(255,255,255,.9);color:var(--ink);font-size:18px;line-height:1;cursor:pointer}
'''
c = c.replace('/* ---------- responsive ---------- */', extra + '\n/* ---------- responsive ---------- */')
css.write_text(c, encoding='utf-8')
print('editor UI added')
