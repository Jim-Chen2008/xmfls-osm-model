  /* ================= first-person walk ================= */
  const WALK = {
    active: false, eye: 1.72, speed: 5.2, run: 9.2,
    jump: 0, vy: 0, grounded: true, latch: false,
    saved: null
  };
  const FLY_HELP = '左键拖动视角 · WASD 移动 · Space 上升 / Shift 下降';
  const WALK_HELP = '左键拖动视角 · WASD 步行 · Shift 加速 · Space 跳跃';

  function pointInPoly(x, z, poly) {
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const xi = poly[i][0], zi = poly[i][1], xj = poly[j][0], zj = poly[j][1];
      const hit = ((zi > z) !== (zj > z)) && (x < (xj - xi) * (z - zi) / (zj - zi) + xi);
      if (hit) inside = !inside;
    }
    return inside;
  }

  function walkBlocked(x, z) {
    scene.updateMatrixWorld();
    const p = new THREE.Vector3();
    const inv = new THREE.Matrix4();
    for (const v of buildingViews) {
      if (!v.inside || !v.group.visible) continue;
      inv.copy(v.group.matrixWorld).invert();
      p.set(x, 0, z).applyMatrix4(inv);
      if (pointInPoly(p.x, p.z, v.rec.polygon)) return true;
    }
    return false;
  }

  function setHelp(text) {
    const el = document.querySelector('#bottom .help');
    if (el) el.textContent = text;
  }

  function enterWalk() {
    if (WALK.active) return;
    WALK.saved = { pos: camera.position.clone(), yaw: fly.yaw, pitch: fly.pitch, fov: camera.fov };
    WALK.active = true;
    WALK.jump = 0; WALK.vy = 0; WALK.grounded = true; WALK.latch = false;
    view.auto = false;
    const auto = $('#autoBtn'); if (auto) auto.classList.remove('active');
    if (camera.position.y > 12) {
      camera.position.set(136, WALK.eye, -96);
      fly.yaw = 2.0;
      fly.pitch = 0;
    } else {
      camera.position.y = WALK.eye;
    }
    camera.fov = 62;
    camera.updateProjectionMatrix();
    document.body.classList.add('walking');
    document.querySelectorAll('.view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === 'walk'));
    setHelp(WALK_HELP);
  }

  function leaveWalk(restore = true) {
    if (!WALK.active) return;
    WALK.active = false;
    document.body.classList.remove('walking');
    if (restore && WALK.saved) {
      camera.position.copy(WALK.saved.pos);
      fly.yaw = WALK.saved.yaw;
      fly.pitch = WALK.saved.pitch;
      camera.fov = WALK.saved.fov;
    } else {
      camera.fov = phoneLayout() ? 50 : 40;
      camera.position.y = Math.max(camera.position.y, 2);
    }
    camera.updateProjectionMatrix();
    document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
    setHelp(FLY_HELP);
  }

