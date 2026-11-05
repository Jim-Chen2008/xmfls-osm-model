from pathlib import Path
p = Path(r'xmfls-osm-model\src\app.js')
s = p.read_text(encoding='utf-8')

# do not draw the OSM pitch that overlaps the track; the six courts are rebuilt below
s = s.replace("  for (const p of DATA.pitches || []) {\n    if (DATA.track && DATA.track.inner && p.id === DATA.track.inner.id) continue;",
              "  for (const p of DATA.pitches || []) {\n    if (DATA.track && DATA.track.inner && p.id === DATA.track.inner.id) continue;\n    if (p.id === '638483883') continue;")

# shift six courts east, away from the track apron
old = """  const bball = (DATA.pitches || []).find(p => p.id === '638483883');
  if (bball) {
    const [x0, x1, z0, z1] = bball.bbox;
    lmAdd(flatPolygon(bball.polygon, .062, LMAT.courtRed), false, true);
    const cols = 2, rows = 3;
    const cw = (x1 - x0) / cols, cd = (z1 - z0) / rows;"""
new = """  const bball = (DATA.pitches || []).find(p => p.id === '638483883');
  if (bball) {
    const z0 = bball.bbox[2], z1 = bball.bbox[3];
    const x0 = -73, x1 = -19;
    lmRect(x1 - x0 + 4, z1 - z0 + 4, LMAT.courtRed, (x0 + x1) / 2, (z0 + z1) / 2, .058);
    const cols = 2, rows = 3;
    const cw = (x1 - x0) / cols, cd = (z1 - z0) / rows;"""
if old not in s: raise SystemExit('bball geometry block not found')
s = s.replace(old, new)

# platform shifted to the track/court edge and narrowed
old_platform = """  (() => {
    const px = -68.5, pz = -35;
    const g = new THREE.Group(); g.position.set(px, 0, pz); G.landmarks.add(g);
    lmBox(10, 1.15, 28, LMAT.concrete, 0, .58, 0, g);
    for (const x of [-4.1, 4.1]) for (const z of [-12, 0, 12]) lmCyl(.17, .2, 6.2, 8, LMAT.metal, x, 3.1, z, g);
    const roof = new THREE.Mesh(new THREE.SphereGeometry(1, 30, 14, 0, Math.PI * 2, 0, Math.PI / 2), LMAT.white);
    roof.scale.set(6.2, 1.45, 15); roof.position.set(0, 6.3, 0); g.add(lmAdd(roof));
    lmBox(10.5, .25, 28.5, LMAT.white, 0, 6.25, 0, g);
    addFeature({ kind: '平台', name: '台下平台 · 膜结构', x: px, z: pz, y: 8, angle: 0, layer: G.landmarks });
  })();"""
new_platform = """  (() => {
    const px = -77, pz = -35;
    const g = new THREE.Group(); g.position.set(px, 0, pz); G.landmarks.add(g);
    lmBox(8, 1.15, 28, LMAT.concrete, 0, .58, 0, g);
    for (const x of [-3.2, 3.2]) for (const z of [-11.5, 0, 11.5]) lmCyl(.17, .2, 6.0, 8, LMAT.metal, x, 3.0, z, g);
    const roof = new THREE.Mesh(new THREE.SphereGeometry(1, 30, 14, 0, Math.PI * 2, 0, Math.PI / 2), LMAT.white);
    roof.scale.set(5.2, 1.4, 14.5); roof.position.set(0, 6.1, 0); g.add(lmAdd(roof));
    lmBox(12, .25, 28.5, LMAT.white, 0, 6.05, 0, g);
    addFeature({ kind: '平台', name: '台下平台 · 膜结构', x: px, z: pz, y: 8, angle: 0, layer: G.landmarks });
  })();"""
if old_platform not in s: raise SystemExit('platform block not found')
s = s.replace(old_platform, new_platform)

p.write_text(s, encoding='utf-8')
print('sports adjusted')
