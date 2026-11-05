from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("  G.grid.rotation.y = CAMPUS_ROT;", "  G.grid.rotation.y = 10.3 * Math.PI / 180;")
# selSub local coords
old="""    $('#selSub').textContent = 'way ' + rec.id + ' · ' + (rec.inside ? '校界内' : '校界外') + (f ? (' · X ' + fmtCoord(f.x) + ' · Z ' + fmtCoord(f.z) + ' · θ ' + f.angle.toFixed(1) + '°') : '');"""
new="""    const lc = f ? worldToLocal(f.x, f.z) : null;
    $('#selSub').textContent = 'way ' + rec.id + ' · ' + (rec.inside ? '校界内' : '校界外') + (f ? (' · X ' + fmtCoord(lc.x) + ' · Z ' + fmtCoord(lc.z) + ' · θ ' + f.angle.toFixed(1) + '°') : '');"""
if old not in s: raise SystemExit('selSub anchor')
s=s.replace(old,new)
# featureCoord local
s=s.replace("  function featureCoord(f) { return 'X ' + fmtCoord(f.x) + ' · Z ' + fmtCoord(f.z) + ' · θ ' + f.angle.toFixed(1) + '°'; }", "  function featureCoord(f) { const lc = worldToLocal(f.x, f.z); return 'X ' + fmtCoord(lc.x) + ' · Z ' + fmtCoord(lc.z) + ' · θ ' + f.angle.toFixed(1) + '°'; }")
p.write_text(s,encoding='utf-8'); print('local coords patches')
