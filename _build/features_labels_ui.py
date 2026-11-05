from pathlib import Path
p = Path(r'xmfls-osm-model\src\app.js')
s = p.read_text(encoding='utf-8')

# ---------- labels block ----------
start = s.index('  /* ---------- labels ---------- */')
end = s.index('  /* ---------- compass ---------- */', start)
new_labels = r'''  /* ---------- feature labels / numbers ---------- */
  const labelDefs = [];
  let labelsOn = true;
  let codesOn = true;
  function addLabel(text, x, y, z, kind = '', layer = null, code = false) {
    const div = document.createElement('div');
    div.className = 'map-label ' + kind;
    div.textContent = text;
    labelsEl.appendChild(div);
    const def = { el: div, x, y, z, kind, layer, code };
    labelDefs.push(def);
    return def;
  }

  const schoolRec = DATA.school;
  addLabel(schoolRec.name || '学校', 0, 28, 0, 'school');
  for (const s of DATA.otherSchools || []) {
    if (s.name) addLabel(s.name, s.centroid[0], 18, s.centroid[1], 'context', G.context);
  }
  const roadNames = new Map();
  for (const r of DATA.roads) {
    if (!r.name) continue;
    const prev = roadNames.get(r.name);
    if (!prev || r.points.length > prev.points.length) roadNames.set(r.name, r);
  }
  for (const [name, r] of roadNames) {
    const mid = r.points[Math.floor(r.points.length / 2)];
    if (Math.abs(mid[0]) < 520 && Math.abs(mid[1]) < 360) addLabel(name, mid[0], 1.2, mid[1], 'road', G.roads);
  }

  // 01–31: numbers on buildings and real-scene landmarks
  for (const f of FEATURES) {
    if (f.kind === '建筑') {
      f.labelDef = addLabel('#' + f.label, f.x, f.y, f.z, 'code' + (f.rec && !f.rec.inside ? ' outside' : ''), f.layer, true);
    } else {
      f.labelDef = addLabel('#' + f.label + ' ' + f.name, f.x, f.y, f.z, 'feature', f.layer, false);
    }
  }

  const labelVec = new THREE.Vector3();
  const camDir = new THREE.Vector3();
  function updateLabels() {
    camera.getWorldDirection(camDir);
    const w = window.innerWidth, h = window.innerHeight;
    for (const l of labelDefs) {
      const visible = (l.code ? codesOn : labelsOn) && (!l.layer || l.layer.visible);
      if (!visible) { l.el.classList.remove('show'); continue; }
      labelVec.set(l.x, l.y, l.z);
      const to = labelVec.clone().sub(camera.position);
      if (to.dot(camDir) <= 0) { l.el.classList.remove('show'); continue; }
      labelVec.project(camera);
      if (labelVec.z > 1 || labelVec.z < -1) { l.el.classList.remove('show'); continue; }
      const sx = (labelVec.x * .5 + .5) * w;
      const sy = (-labelVec.y * .5 + .5) * h;
      if (sx < -100 || sx > w + 100 || sy < -40 || sy > h + 40) { l.el.classList.remove('show'); continue; }
      l.el.style.left = sx + 'px';
      l.el.style.top = sy + 'px';
      l.el.classList.add('show');
    }
  }

  function fmtCoord(v) { return (v >= 0 ? '+' : '') + v.toFixed(1); }
  function featureCoord(f) { return 'X ' + fmtCoord(f.x) + ' · Z ' + fmtCoord(f.z) + ' · θ ' + f.angle.toFixed(1) + '°'; }

  /* ---------- index list ---------- */
  function updateIndex() {
    const list = $('#indexList');
    if (!list) return;
    list.textContent = '';
    for (const f of FEATURES) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'idx-row';
      const no = document.createElement('b'); no.textContent = '#' + f.label;
      const nm = document.createElement('span');
      nm.textContent = (f.rec && f.rec.name ? f.rec.name : f.name) + (f.rec && !f.rec.inside ? ' · 校外' : '');
      const em = document.createElement('em'); em.textContent = 'θ ' + f.angle.toFixed(1) + '°';
      const co = document.createElement('i'); co.textContent = 'X ' + fmtCoord(f.x) + ' · Z ' + fmtCoord(f.z);
      btn.append(no, nm, em, co);
      btn.title = '定位到 #' + f.label;
      btn.addEventListener('click', () => {
        $$('.idx-row').forEach(x => x.classList.remove('active'));
        btn.classList.add('active');
        focusFeature(f);
        if (f.rec) showBuilding(f.rec);
        else $('#dbgSel').textContent = '#' + f.label + ' ' + f.name + ' · ' + featureCoord(f);
      });
      list.appendChild(btn);
    }
    $('#indexCount').textContent = FEATURES.length;
  }
  updateIndex();

  /* ---------- debug HUD ---------- */
  const dbgCam = $('#dbgCam'), dbgAng = $('#dbgAng'), dbgGround = $('#dbgGround'), dbgSel = $('#dbgSel');
  const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  const groundRay = new THREE.Raycaster();
  const groundNdc = new THREE.Vector2();
  const groundHit = new THREE.Vector3();
  function setGroundFromPointer(clientX, clientY) {
    if (!dbgGround) return;
    const nd = screenToNdc(clientX, clientY);
    groundNdc.set(nd.x, nd.y);
    groundRay.setFromCamera(groundNdc, camera);
    if (groundRay.ray.intersectPlane(groundPlane, groundHit)) {
      dbgGround.textContent = 'X ' + fmtCoord(groundHit.x) + '  Z ' + fmtCoord(groundHit.z);
    } else {
      dbgGround.textContent = 'X —  Z —';
    }
  }
  function updateDebugHud() {
    if (!dbgCam) return;
    dbgCam.textContent = 'X ' + fmtCoord(camera.position.x) + '  Y ' + camera.position.y.toFixed(1) + '  Z ' + fmtCoord(camera.position.z);
    const heading = (((-fly.yaw * 180 / Math.PI) % 360) + 360) % 360;
    dbgAng.textContent = 'HDG ' + heading.toFixed(1) + '° / PITCH ' + (fly.pitch * 180 / Math.PI).toFixed(1) + '°';
  }

'''
s = s[:start] + new_labels + s[end:]

# ---------- aim/focus functions ----------
anchor = "  /* ---------- pointer / orbit ---------- */"
focus_code = r'''  function aimAtPoint(x, y, z) {
    const dir = new THREE.Vector3(x, y, z).sub(camera.position);
    if (dir.lengthSq() < .001) return;
    dir.normalize();
    fly.pitch = Math.asin(clamp(dir.y, -1, 1));
    fly.yaw = Math.atan2(-dir.x, -dir.z);
    camera.rotation.set(fly.pitch, fly.yaw, 0, 'YXZ');
  }
  function focusFeature(f) {
    const wide = f.kind === '场地' || f.kind === '球场' || f.kind === '边界';
    const off = wide ? 155 : (f.kind === '建筑' ? 68 : 48);
    const targetY = f.kind === '建筑' ? Math.min(height * .5, 7) : 2.2;
    camera.position.set(f.x + off * .66, Math.max(26, off * .55), f.z + off * .66);
    aimAtPoint(f.x, targetY, f.z);
    view.userMoved = true;
    view.auto = false;
    const auto = $('#autoBtn'); if (auto) auto.classList.remove('active');
  }

'''
if anchor not in s: raise SystemExit('pointer anchor missing')
s = s.replace(anchor, focus_code + anchor)

# ---------- showBuilding number/coords ----------
s = s.replace("      selectedRec = null;\n      block.hidden = true;\n      empty.hidden = false;\n      $('#clearSelection').hidden = true;\n      refreshHighlight();\n      return;", "      selectedRec = null;\n      block.hidden = true;\n      empty.hidden = false;\n      $('#clearSelection').hidden = true;\n      if (dbgSel) dbgSel.textContent = '—';\n      refreshHighlight();\n      return;")
s = s.replace("    $('#selTitle').textContent = rec.name || ('OSM 建筑 · ' + rec.id);\n    $('#selSub').textContent = 'way ' + rec.id + ' · ' + (rec.inside ? '校界内' : '校界外') + ' · ' + (rec.tags.building || 'building');", "    const f = FEATURE_BY_REC.get(rec);\n    $('#selTitle').textContent = f ? ('#' + f.label + ' · ' + (rec.name || 'OSM 建筑')) : (rec.name || ('OSM 建筑 · ' + rec.id));\n    $('#selSub').textContent = 'way ' + rec.id + ' · ' + (rec.inside ? '校界内' : '校界外') + (f ? (' · X ' + fmtCoord(f.x) + ' · Z ' + fmtCoord(f.z) + ' · θ ' + f.angle.toFixed(1) + '°') : '');\n    if (dbgSel && f) dbgSel.textContent = '#' + f.label + ' ' + (rec.name || '建筑') + ' · ' + featureCoord(f);")

# ---------- height slider label y ----------
s = s.replace("    for (const v of buildingViews) v.group.scale.y = height;\n    if (selectedRec) $('#selHeight').textContent = height + ' m（示意）';", "    for (const v of buildingViews) v.group.scale.y = height;\n    for (const f of FEATURES) {\n      if (f.kind === '建筑') {\n        f.y = height + 2.5;\n        if (f.labelDef) f.labelDef.y = f.y;\n      }\n    }\n    if (selectedRec) $('#selHeight').textContent = height + ' m（示意）';")

# ---------- layer toggles ----------
s = s.replace("      if (k === 'context') G.context.visible = input.checked;\n      if (k === 'grid') G.grid.visible = input.checked;\n      if (k === 'labels') labelsOn = input.checked;", "      if (k === 'context') G.context.visible = input.checked;\n      if (k === 'landmarks') G.landmarks.visible = input.checked;\n      if (k === 'guide') G.guide.visible = input.checked;\n      if (k === 'grid') G.grid.visible = input.checked;\n      if (k === 'labels') labelsOn = input.checked;\n      if (k === 'codes') codesOn = input.checked;")

# ---------- ground debug on pointer move / leave ----------
s = s.replace("  el.addEventListener('pointermove', e => {\n    if (e.pointerType === 'touch') { touchPointerMove(e); return; }", "  el.addEventListener('pointermove', e => {\n    setGroundFromPointer(e.clientX, e.clientY);\n    if (e.pointerType === 'touch') { touchPointerMove(e); return; }")
s = s.replace("  el.addEventListener('pointerup', e => {", "  el.addEventListener('pointerleave', () => { if (dbgGround) dbgGround.textContent = 'X —  Z —'; });\n  el.addEventListener('pointerup', e => {")

# ---------- debug update in animate ----------
s = s.replace("    updateCompass();\n    updateLabels();\n    renderer.render(scene, camera);", "    updateCompass();\n    updateDebugHud();\n    updateLabels();\n    renderer.render(scene, camera);")

# expose features for debugging
s = s.replace("window.__MODEL = { scene, camera, renderer, view, fly, buildingViews, showBuilding, G, sun, height: () => height };", "window.__MODEL = { scene, camera, renderer, view, fly, buildingViews, showBuilding, G, sun, FEATURES, focusFeature, height: () => height };")

p.write_text(s, encoding='utf-8')
print('labels/index/debug patched')
