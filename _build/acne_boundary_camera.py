from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
# building self-shadow off to remove acne stripes
s=s.replace("    walls.castShadow = true;\n    walls.receiveShadow = true;", "    walls.castShadow = true;\n    walls.receiveShadow = false;")
s=s.replace("      roof.castShadow = true;\n      roof.receiveShadow = true;", "      roof.castShadow = true;\n      roof.receiveShadow = false;")
# boundary band helper
anchor="  function lineLoop(points, y, material) {"
helper="""  function flatRibbon(points, width, y, material) {
    const pts = cleanRing(points);
    if (pts.length < 3) return null;
    const pos = []; const idx = [];
    const half = width / 2;
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = pts[(i + 1) % pts.length];
      const dx = b[0] - a[0], dz = b[1] - a[1];
      const L = Math.hypot(dx, dz);
      if (L < .01) continue;
      const nx = -dz / L * half, nz = dx / L * half;
      const base = pos.length / 3;
      pos.push(a[0] + nx, y, a[1] + nz, b[0] + nx, y, b[1] + nz, b[0] - nx, y, b[1] - nz, a[0] - nx, y, a[1] - nz);
      idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    const ns = []; for (let i = 0; i < pos.length; i += 3) ns.push(0, 1, 0);
    g.setAttribute('normal', new THREE.Float32BufferAttribute(ns, 3));
    g.setIndex(idx);
    const m = new THREE.Mesh(g, material);
    m.receiveShadow = false;
    return m;
  }

"""
s=s.replace(anchor, helper+anchor)
# add school boundary ribbon after ground
anchor2="  G.ground.add(lineLoop(DATA.school.polygon, .036, schoolLineMat));"
addition=anchor2+"\n  const boundaryBand = flatRibbon(DATA.school.polygon, 1.0, .034, new THREE.MeshStandardMaterial({ color: 0x596652, roughness: .95, transparent: true, opacity: .42, side: THREE.DoubleSide }));\n  if (boundaryBand) G.ground.add(boundaryBand);"
s=s.replace(anchor2, addition)
# camera
s=s.replace("const home = { target: new THREE.Vector3(44, 3, -4), theta: .69, phi: 1.04, radius: 490 };", "const home = { target: new THREE.Vector3(70, 3, -4), theta: .69, phi: 1.04, radius: 550 };")
p.write_text(s,encoding='utf-8')
print('patched')
