from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
walk=Path(r'xmfls-osm-model\_build\walk_mode.js').read_text(encoding='utf-8')
anchor="  /* ---------- pointer / orbit ---------- */"
if anchor not in s: raise SystemExit('pointer anchor')
s=s.replace(anchor, walk+'\n'+anchor,1)
# setView walk
s=s.replace("  function setView(name) {\n    let target, theta, phi, radius;", "  function setView(name) {\n    if (name === 'walk') { enterWalk(); return; }\n    if (WALK.active) leaveWalk(false);\n    let target, theta, phi, radius;")
# animate branch
old="""    moveWish.set(0, 0, 0).addScaledVector(moveForward, iz).addScaledVector(moveRight, ix);
    if (moveWish.lengthSq() > 1) moveWish.normalize();
    if (moveWish.lengthSq() > 0) camera.position.addScaledVector(moveWish, fly.speed * dt);

    const vy = (keys.Space ? 1 : 0) - ((keys.ShiftLeft || keys.ShiftRight) ? 1 : 0);
    camera.position.y += vy * fly.vertical * dt;
    camera.position.y = clamp(camera.position.y, 2, 700);
    camera.rotation.set(fly.pitch, fly.yaw, 0, 'YXZ');"""
new="""    moveWish.set(0, 0, 0).addScaledVector(moveForward, iz).addScaledVector(moveRight, ix);
    if (moveWish.lengthSq() > 1) moveWish.normalize();
    if (WALK.active) {
      const speed = (keys.ShiftLeft || keys.ShiftRight) ? WALK.run : WALK.speed;
      const dx = moveWish.x * speed * dt, dz = moveWish.z * speed * dt;
      if (dx || dz) {
        const nx = camera.position.x + dx, nz = camera.position.z + dz;
        if (!walkBlocked(nx, nz)) { camera.position.x = nx; camera.position.z = nz; }
        else {
          if (!walkBlocked(nx, camera.position.z)) camera.position.x = nx;
          if (!walkBlocked(camera.position.x, nz)) camera.position.z = nz;
        }
      }
      if (keys.Space && !WALK.latch && WALK.grounded) { WALK.vy = 4.4; WALK.grounded = false; }
      WALK.latch = !!keys.Space;
      if (!WALK.grounded) {
        WALK.vy -= 11.5 * dt;
        WALK.jump += WALK.vy * dt;
        if (WALK.jump <= 0) { WALK.jump = 0; WALK.vy = 0; WALK.grounded = true; }
      }
      camera.position.y = WALK.eye + WALK.jump + .012;
    } else {
      if (moveWish.lengthSq() > 0) camera.position.addScaledVector(moveWish, fly.speed * dt);
      const vy = (keys.Space ? 1 : 0) - ((keys.ShiftLeft || keys.ShiftRight) ? 1 : 0);
      camera.position.y += vy * fly.vertical * dt;
      camera.position.y = clamp(camera.position.y, 2, 700);
    }
    camera.rotation.set(fly.pitch, fly.yaw, 0, 'YXZ');"""
if old not in s: raise SystemExit('animate block')
s=s.replace(old,new)
# focus feature leave walk
s=s.replace("  function focusFeature(f) {\n    const wide", "  function focusFeature(f) {\n    if (WALK.active) leaveWalk(false);\n    const wide")
# help button via view handler already setView
p.write_text(s,encoding='utf-8'); print('walk integrated')
