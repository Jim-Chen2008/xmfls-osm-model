from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
# helpers before updateIndex
anchor="  /* ---------- index list ---------- */"
helpers=r'''  /* ---------- campus-local coordinates (screen-straight in 摆正 view) ---------- */
  const LOCAL_ROT = CAMPUS_ROT;
  const LOCAL_C = Math.cos(LOCAL_ROT), LOCAL_S = Math.sin(LOCAL_ROT);
  function worldToLocal(x, z) { return { x: x * LOCAL_C - z * LOCAL_S, z: x * LOCAL_S + z * LOCAL_C }; }
  function localToWorld(x, z) { return { x: x * LOCAL_C + z * LOCAL_S, z: -x * LOCAL_S + z * LOCAL_C }; }

'''
if anchor not in s: raise SystemExit('index anchor')
s=s.replace(anchor, helpers+anchor,1)
# index coords local
s=s.replace("      const co = document.createElement('i'); co.textContent = 'X ' + fmtCoord(f.x) + ' · Z ' + fmtCoord(f.z);", "      const lc = worldToLocal(f.x, f.z);\n      const co = document.createElement('i'); co.textContent = 'X ' + fmtCoord(lc.x) + ' · Z ' + fmtCoord(lc.z);")
# editor target local state
old="""    const geomX = f.x - g.position.x;
    const geomZ = f.z - g.position.z;
    const baseLabelY = f.labelDef ? f.labelDef.y : f.y;
    const state = {
      x: f.x, z: f.z, y: g.position.y,
      rot: g.rotation.y, h: g.scale.y
    };"""
new="""    const geomX = f.x - g.position.x;
    const geomZ = f.z - g.position.z;
    const lc0 = worldToLocal(f.x, f.z);
    const baseLabelY = f.labelDef ? f.labelDef.y : f.y;
    const state = {
      x: lc0.x, z: lc0.z, y: g.position.y,
      rot: g.rotation.y, h: g.scale.y
    };"""
if old not in s: raise SystemExit('state anchor')
s=s.replace(old,new)
# apply target world conversion
old2="""  function applyTarget(t) {
    const s = t.state;
    t.group.position.x = s.x - t.geomX;
    t.group.position.z = s.z - t.geomZ;
    t.group.position.y = s.y;
    t.group.rotation.y = s.rot;
    t.group.scale.y = s.h;
    if (t.isEllipse) {
      t.group.scale.x = (s.rx / 2) / 57.6418;
      t.group.scale.z = (s.rz / 2) / 18.5498;
    }
    t.f.x = s.x; t.f.z = s.z;
    if (t.f.labelDef) {
      t.f.labelDef.x = s.x;
      t.f.labelDef.z = s.z;"""
new2="""  function applyTarget(t) {
    const s = t.state;
    const w = localToWorld(s.x, s.z);
    t.group.position.x = w.x - t.geomX;
    t.group.position.z = w.z - t.geomZ;
    t.group.position.y = s.y;
    t.group.rotation.y = s.rot;
    t.group.scale.y = s.h;
    if (t.isEllipse) {
      t.group.scale.x = (s.rx / 2) / 57.6418;
      t.group.scale.z = (s.rz / 2) / 18.5498;
    }
    t.f.x = w.x; t.f.z = w.z;
    if (t.f.labelDef) {
      t.f.labelDef.x = w.x;
      t.f.labelDef.z = w.z;"""
if old2 not in s: raise SystemExit('apply anchor')
s=s.replace(old2,new2)
# feature label y uses no s.x; no other direct state x labels? search selected debug later
# commit update index (append in commitHistory)
s=s.replace("    saveLocal();\n    updateHistoryButtons();\n    setEditStatus('已记录修改');", "    saveLocal();\n    updateHistoryButtons();\n    if (typeof updateIndex === 'function') updateIndex();\n    setEditStatus('已记录修改');")
# copy pose local + world
old3="""  function poseText() {
    const heading = (((-fly.yaw * 180 / Math.PI) % 360) + 360) % 360;
    const pitch = fly.pitch * 180 / Math.PI;
    return 'X ' + camera.position.x.toFixed(2) + ', Z ' + camera.position.z.toFixed(2) +
      ', Y ' + camera.position.y.toFixed(2) + ', HDG ' + heading.toFixed(2) + '°, PITCH ' + pitch.toFixed(2) + '°' +
      (WALK.active ? ' [第一人称]' : ' [飞行]');
  }"""
new3="""  function poseText() {
    const heading = (((-fly.yaw * 180 / Math.PI) % 360) + 360) % 360;
    const pitch = fly.pitch * 180 / Math.PI;
    const lc = worldToLocal(camera.position.x, camera.position.z);
    return 'X ' + lc.x.toFixed(2) + ', Z ' + lc.z.toFixed(2) +
      ', Y ' + camera.position.y.toFixed(2) + ', HDG ' + heading.toFixed(2) + '°, PITCH ' + pitch.toFixed(2) + '°' +
      ' (场地坐标; OSM ' + camera.position.x.toFixed(2) + ', ' + camera.position.z.toFixed(2) + ')' +
      (WALK.active ? ' [第一人称]' : ' [飞行]');
  }"""
if old3 not in s: raise SystemExit('pose anchor')
s=s.replace(old3,new3)
# rotate grid to local screen axes
s=s.replace("  G.grid.position.y = .026;", "  G.grid.position.y = .026;\n  G.grid.rotation.y = CAMPUS_ROT;")
p.write_text(s,encoding='utf-8'); print('local frame applied')
