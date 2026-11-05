from pathlib import Path
p = Path(r'xmfls-osm-model\src\app.js')
s = p.read_text(encoding='utf-8')
old = "  const home = { target: new THREE.Vector3(86, 3, -4), theta: .69, phi: 1.04, radius: 560 };"
new = """  function phoneLayout() { return window.innerWidth < 760 || window.innerHeight > window.innerWidth * 1.2; }
  const phone0 = phoneLayout();
  camera.fov = phone0 ? 50 : 40;
  camera.updateProjectionMatrix();
  const home = {
    target: new THREE.Vector3(phone0 ? 0 : 86, 3, phone0 ? 0 : -4),
    theta: .69,
    phi: phone0 ? 1.0 : 1.04,
    radius: phone0 ? 1000 : 560
  };"""
if old not in s: raise SystemExit('home anchor missing')
s = s.replace(old, new)
# userMoved state
s = s.replace("    auto: false\n  };", "    auto: false,\n    userMoved: false\n  };")
# mark moved on wheel, pointer, touch
s = s.replace("    view.goalRadius = clamp(view.goalRadius * Math.exp(e.deltaY * .0011), 120, 1800);", "    view.userMoved = true;\n    view.goalRadius = clamp(view.goalRadius * Math.exp(e.deltaY * .0011), 120, 1800);")
s = s.replace("    if (view.auto) { view.auto = false; $('#autoBtn').classList.remove('active'); }\n  });\n\n  el.addEventListener('pointermove'", "    view.userMoved = true;\n    if (view.auto) { view.auto = false; $('#autoBtn').classList.remove('active'); }\n  });\n\n  el.addEventListener('pointermove'")
s = s.replace("    if (pointers.size === 1) {\n      drag = { mode: 'rotate'", "    view.userMoved = true;\n    if (pointers.size === 1) {\n      drag = { mode: 'rotate'")
# top view radius responsive
s = s.replace("      view.goalRadius = 610;", "      view.goalRadius = phoneLayout() ? 910 : 610;")
# resize fov and reset home only if user has not moved
old_resize = """  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });"""
new_resize = """  window.addEventListener('resize', () => {
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
if old_resize not in s: raise SystemExit('resize block missing')
s = s.replace(old_resize, new_resize)
p.write_text(s, encoding='utf-8')

html = Path(r'xmfls-osm-model\src\index.html')
h = html.read_text(encoding='utf-8')
icon = '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 32 32\'%3E%3Crect width=\'32\' height=\'32\' rx=\'6\' fill=\'%23436451\'/%3E%3Cpath d=\'M8 24V8h4l8 10V8h4v16h-4L12 14v10z\' fill=\'%23f6f0e4\'/%3E%3C/svg%3E">'
h = h.replace('<link rel="stylesheet" href="style.css">', icon + '\n<link rel="stylesheet" href="style.css">')
html.write_text(h, encoding='utf-8')
print('responsive camera + favicon')
