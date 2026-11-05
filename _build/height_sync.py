from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
old="""    for (const f of FEATURES) {
      if (f.kind === '建筑') {
        f.y = height + 2.5;
        if (f.labelDef) f.labelDef.y = f.y;
      }
    }"""
new="""    for (const f of FEATURES) {
      if (f.kind === '建筑') {
        f.y = height + 2.5;
        if (f.labelDef) f.labelDef.y = f.y;
        if (f.edit) {
          f.edit.state.h = height;
          f.edit.initial.h = height;
          f.edit.state.y = 0;
        }
      }
    }"""
if old not in s: raise SystemExit('height loop missing')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8'); print('height sync')
