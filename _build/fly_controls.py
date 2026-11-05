from pathlib import Path
p = Path(r'xmfls-osm-model\src\app.js')
s = p.read_text(encoding='utf-8')

# 1) replace the orbit view block with a free-fly camera
start = s.index("  /* ---------- view / orbit ---------- */")
end = s.index("  /* ---------- pointer / orbit ---------- */", start)
new_view = r'''  /* ---------- free-fly camera ---------- */
  function phoneLayout() { return window.innerWidth < 760 || window.innerHeight > window.innerWidth * 1.2; }
  const phone0 = phoneLayout();
  camera.fov = phone0 ? 50 : 40;
  camera.rotation.order = 'YXZ';
  camera.updateProjectionMatrix();
  const home = {
    target: new THREE.Vector3(phone0 ? 0 : 86, 3, phone0 ? 0 : -4),
    theta: .69,
    phi: phone0 ? 1.0 : 1.04,
    radius: phone0 ? 1000 : 560
  };
  const view = { auto: false, userMoved: false };
  const fly = { yaw: 0, pitch: 0, speed: 54, vertical: 36 };

  function orbitPos(target, theta, phi, radius) {
    const sp = Math.sin(phi);
    return new THREE.Vector3(
      target.x + radius * sp * Math.sin(theta),
      target.y + radius * Math.cos(phi),
      target.z + radius * sp * Math.cos(theta)
    );
  }
  function setCameraTo(target, theta, phi, radius) {
    camera.position.copy(orbitPos(target, theta, phi, radius));
    const dir = target.clone().sub(camera.position).normalize();
    fly.pitch = Math.asin(clamp(dir.y, -1, 1));
    fly.yaw = Math.atan2(-dir.x, -dir.z);
    camera.rotation.set(fly.pitch, fly.yaw, 0, 'YXZ');
  }
  setCameraTo(home.target, home.theta, home.phi, home.radius);

  function setView(name) {
    let target, theta, phi, radius;
    if (name === 'top') {
      target = new THREE.Vector3(0, 0, 0);
      theta = 0;
      phi = .055;
      radius = phoneLayout() ? 910 : 610;
    } else {
      target = home.target.clone();
      theta = home.theta;
      phi = home.phi;
      radius = home.radius;
    }
    setCameraTo(target, theta, phi, radius);
    view.auto = false;
    $('#autoBtn').classList.remove('active');
    $$('.view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === (name === 'top' ? 'top' : 'overview')));
  }

'''
s = s[:start] + new_view + s[end:]

# 2) pointerdown: left button only, look mode
s = s.replace("    if (e.button !== 0 && e.button !== 2) return;\n    drag = {\n      mode: (e.button === 2 || e.shiftKey) ? 'pan' : 'rotate',\n      x: e.clientX, y: e.clientY, lastX: e.clientX, lastY: e.clientY,\n      moved: 0\n    };", "    if (e.button !== 0) return;\n    drag = {\n      mode: 'look',\n      x: e.clientX, y: e.clientY, lastX: e.clientX, lastY: e.clientY,\n      moved: 0\n    };")

# 3) pointermove: look with free-fly yaw/pitch
s = s.replace("      if (drag.mode === 'rotate') {\n        view.goalTheta -= dx * .006;\n        view.goalPhi = clamp(view.goalPhi - dy * .006, .06, 1.48);\n      } else {\n        panView(dx, dy);\n      }\n      return;", "      fly.yaw -= dx * .0038;\n      fly.pitch = clamp(fly.pitch - dy * .0038, -1.45, 1.45);\n      return;")

# 4) remove panView and disable wheel; replace touch handlers with one-finger look
start = s.index("  function panView(dx, dy) {")
end = s.index("  /* ---------- labels ---------- */", start)
new_controls = r'''  el.addEventListener('wheel', e => {
    // 本次只保留用户指定的控制方式：拖动 + WASD + Space / Shift
    e.preventDefault();
  }, { passive: false });

  /* ---------- touch: one-finger look ---------- */
  function touchPointerDown(e) {
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    el.setPointerCapture(e.pointerId);
    view.userMoved = true;
    if (pointers.size === 1) {
      drag = { mode: 'look', x: e.clientX, y: e.clientY, lastX: e.clientX, lastY: e.clientY, moved: 0 };
      if (view.auto) { view.auto = false; $('#autoBtn').classList.remove('active'); }
    }
  }
  function touchPointerMove(e) {
    if (!pointers.has(e.pointerId)) return;
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (drag) {
      const dx = e.clientX - drag.lastX;
      const dy = e.clientY - drag.lastY;
      drag.lastX = e.clientX; drag.lastY = e.clientY;
      drag.moved += Math.abs(dx) + Math.abs(dy);
      fly.yaw -= dx * .0042;
      fly.pitch = clamp(fly.pitch - dy * .0042, -1.45, 1.45);
    }
  }
  function touchPointerUp(e) {
    const wasDrag = drag;
    pointers.delete(e.pointerId);
    if (wasDrag && wasDrag.moved < 9 && pointers.size === 0) {
      const rec = pickAt(e.clientX, e.clientY);
      showBuilding(rec);
    }
    if (!pointers.size) drag = null;
  }

  /* ---------- keyboard: WASD move, Space / Shift altitude ---------- */
  const keys = Object.create(null);
  const moveKeys = { KeyW: true, KeyA: true, KeyS: true, KeyD: true, Space: true, ShiftLeft: true, ShiftRight: true };
  function typingTarget(t) {
    if (!t) return false;
    const tag = (t.tagName || '').toUpperCase();
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || t.isContentEditable;
  }
  window.addEventListener('keydown', e => {
    if (typingTarget(e.target)) return;
    if (moveKeys[e.code]) {
      if (e.code === 'Space') e.preventDefault();
      keys[e.code] = true;
    }
  });
  window.addEventListener('keyup', e => {
    if (moveKeys[e.code]) keys[e.code] = false;
  });
  window.addEventListener('blur', () => { for (const k in keys) keys[k] = false; });

'''
s = s[:start] + new_controls + s[end:]

# 5) resize: no orbit state
old_resize = """  window.addEventListener('resize', () => {
    const phone = phoneLayout();
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.fov = phone ? 50 : 40;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    if (!view.userMoved) {
      home.target.set(phone ? 0 : 86, 3, phone ? 0 : -4);
      home.phi = phone ? 1.0 : 1.04;
      home.radius = phone ? 1000 : 560;
      view.goalTarget.copy(home.target);
      view.goalTheta = home.theta;
      view.goalPhi = home.phi;
      view.goalRadius = home.radius;
    }
  });"""
new_resize = """  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.fov = phoneLayout() ? 50 : 40;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });"""
if old_resize not in s: raise SystemExit('resize block missing')
s = s.replace(old_resize, new_resize)

# 6) animate: free-flight movement
old_anim = """  const clock = new THREE.Clock();
  function animate() {
    requestAnimationFrame(animate);
    const dt = Math.min(clock.getDelta(), .05);
    if (view.auto) view.goalTheta += dt * .065;
    const damp = 1 - Math.exp(-8 * dt);
    view.theta += (view.goalTheta - view.theta) * damp;
    view.phi += (view.goalPhi - view.phi) * damp;
    view.radius += (view.goalRadius - view.radius) * damp;
    view.target.lerp(view.goalTarget, damp);
    applyCamera();
    updateCompass();
    updateLabels();
    renderer.render(scene, camera);
  }"""
new_anim = """  const clock = new THREE.Clock();
  const moveForward = new THREE.Vector3();
  const moveRight = new THREE.Vector3();
  const moveWish = new THREE.Vector3();
  function animate() {
    requestAnimationFrame(animate);
    const dt = Math.min(clock.getDelta(), .05);
    if (view.auto) fly.yaw += dt * .08;

    moveForward.set(-Math.sin(fly.yaw), 0, -Math.cos(fly.yaw));
    moveRight.set(Math.cos(fly.yaw), 0, -Math.sin(fly.yaw));
    let ix = (keys.KeyD ? 1 : 0) - (keys.KeyA ? 1 : 0);
    let iz = (keys.KeyW ? 1 : 0) - (keys.KeyS ? 1 : 0);
    moveWish.set(0, 0, 0).addScaledVector(moveForward, iz).addScaledVector(moveRight, ix);
    if (moveWish.lengthSq() > 1) moveWish.normalize();
    if (moveWish.lengthSq() > 0) camera.position.addScaledVector(moveWish, fly.speed * dt);

    const vy = (keys.Space ? 1 : 0) - ((keys.ShiftLeft || keys.ShiftRight) ? 1 : 0);
    camera.position.y += vy * fly.vertical * dt;
    camera.position.y = clamp(camera.position.y, 2, 700);
    camera.rotation.set(fly.pitch, fly.yaw, 0, 'YXZ');

    updateCompass();
    updateLabels();
    renderer.render(scene, camera);
  }"""
if old_anim not in s: raise SystemExit('animate block missing')
s = s.replace(old_anim, new_anim)

# 7) expose fly for diagnostics
s = s.replace("window.__MODEL = { scene, camera, renderer, view, buildingViews, showBuilding, G, sun, height: () => height };", "window.__MODEL = { scene, camera, renderer, view, fly, buildingViews, showBuilding, G, sun, height: () => height };")

p.write_text(s, encoding='utf-8')

# 8) update help text
html = Path(r'xmfls-osm-model\src\index.html')
h = html.read_text(encoding='utf-8')
h = h.replace('左键旋转 · 右键 / Shift 平移 · 滚轮缩放', '左键拖动视角 · WASD 移动 · Space 上升 / Shift 下降')
html.write_text(h, encoding='utf-8')
print('fly controls patched')
