from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
logic=Path(r'xmfls-osm-model\_build\editor_logic.js').read_text(encoding='utf-8')
anchor="  /* ---------- compass ---------- */"
if anchor not in s: raise SystemExit('compass anchor missing')
s=s.replace(anchor, logic+'\n'+anchor,1)
# index click edit branch
old="""        $$('.idx-row').forEach(x => x.classList.remove('active'));
        btn.classList.add('active');
        focusFeature(f);
        if (f.rec) showBuilding(f.rec);"""
new="""        $$('.idx-row').forEach(x => x.classList.remove('active'));
        btn.classList.add('active');
        if (editorMode && f.edit) { selectEditTarget(f.edit); return; }
        focusFeature(f);
        if (f.rec) showBuilding(f.rec);"""
if old not in s: raise SystemExit('index click block missing')
s=s.replace(old,new)
# pointerup edit branch
old2="""    if (drag) {
      const rec = drag.moved < 6 ? pickAt(e.clientX, e.clientY) : null;
      if (drag.moved < 6) showBuilding(rec);
      drag = null;
    }"""
new2="""    if (drag) {
      if (drag.moved < 6) {
        if (editorMode) {
          const t = pickEditTarget(e.clientX, e.clientY);
          if (t) selectEditTarget(t);
        } else {
          const rec = pickAt(e.clientX, e.clientY);
          showBuilding(rec);
        }
      }
      drag = null;
    }"""
if old2 not in s: raise SystemExit('pointerup block missing')
s=s.replace(old2,new2)
p.write_text(s,encoding='utf-8'); print('editor logic inserted')
