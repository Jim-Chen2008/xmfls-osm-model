from pathlib import Path
p = Path(r'xmfls-osm-model\src\app.js')
s = p.read_text(encoding='utf-8')

# constants + yellow plaza material
s = s.replace("  const CAMPUS_ROT = THREE.MathUtils.degToRad(10.3);\n  const CAMPUS_BEARING = 169.7;",
              "  const CAMPUS_ROT = THREE.MathUtils.degToRad(10.3);\n  const CAMPUS_BEARING = 169.7;\n  const TRACK_SHIFT_X = -2;\n  G.sports.position.x = TRACK_SHIFT_X;")
s = s.replace("  function makeStoneTexture() {",
              """  function makeYellowGridTexture() {
    const c = document.createElement('canvas'); c.width = 512; c.height = 512;
    const x = c.getContext('2d');
    x.fillStyle = '#d9c58f'; x.fillRect(0, 0, 512, 512);
    const n = 8, step = 512 / n;
    x.strokeStyle = 'rgba(150,125,72,.55)'; x.lineWidth = 2;
    for (let i = 0; i <= n; i++) {
      x.beginPath(); x.moveTo(i * step, 0); x.lineTo(i * step, 512); x.stroke();
      x.beginPath(); x.moveTo(0, i * step); x.lineTo(512, i * step); x.stroke();
    }
    for (let i = 0; i < 140; i++) {
      x.fillStyle = 'rgba(120,95,45,' + (Math.random() * .05) + ')';
      x.fillRect(Math.random() * 512, Math.random() * 512, 2, 2);
    }
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(7, 7); t.anisotropy = 4;
    return t;
  }
  LMAT.plaza = new THREE.MeshStandardMaterial({ map: makeYellowGridTexture(), roughness: .92, metalness: .01 });
  function makeStoneTexture() {""")

# track/field feature x shift
s = s.replace("addFeature({ kind: '场地', name: '田径场', x: outerC[0], z: outerC[1] + 23, y: 2.4, angle: CAMPUS_BEARING, layer: G.sports });",
              "addFeature({ kind: '场地', name: '田径场', x: outerC[0] + TRACK_SHIFT_X, z: outerC[1] + 23, y: 2.4, angle: CAMPUS_BEARING, layer: G.sports });")
s = s.replace("addFeature({ kind: '场地', name: '足球场', x: innerC[0], z: innerC[1] - 21, y: 2.4, angle: CAMPUS_BEARING, layer: G.sports });",
              "addFeature({ kind: '场地', name: '足球场', x: innerC[0] + TRACK_SHIFT_X, z: innerC[1] - 21, y: 2.4, angle: CAMPUS_BEARING, layer: G.sports });")

# tennis: use the two user points as the bounding block, two courts stacked along z
old_tennis_start = s.index('  // 25–26: two tennis courts')
old_tennis_end = s.index('  // 27: covered grandstand', old_tennis_start)
new_tennis = r'''  // 25–26: two tennis courts from the user's (-171.40,53.74) — (-140.82,119.51) block
  const tennisDefs = [
    { name: '网球场 A', x: -156.11, z: 70.18 },
    { name: '网球场 B', x: -156.11, z: 103.07 }
  ];
  for (const tf of tennisDefs) {
    const cw = 24, cd = 30;
    const g = new THREE.Group(); g.position.set(tf.x, 0, tf.z); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);
    lmRect(cw + 3, cd + 3, LMAT.courtRed, 0, 0, .058, g);
    lmRect(cw, cd, LMAT.tennis, 0, 0, .066, g);
    const pts = [[-cw / 2, -cd / 2], [cw / 2, -cd / 2], [cw / 2, cd / 2], [-cw / 2, cd / 2]];
    g.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts.map(p => new THREE.Vector3(p[0], .073, p[1]))), LMAT.line));
    const net = new THREE.Mesh(new THREE.PlaneGeometry(cw - 1, .82), LMAT.net);
    net.position.set(0, 1.1, 0); g.add(lmAdd(net, false, false));
    for (const s of [-1, 1]) lmCyl(.08, .1, 1.3, 6, LMAT.metal, s * (cw / 2 - .5), .65, 0, g);
    g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, .074, -cd / 2), new THREE.Vector3(0, .074, cd / 2)
    ]), LMAT.line));
    addFeature({ kind: '球场', name: tf.name, x: tf.x, z: tf.z, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });
  }

'''
s = s[:old_tennis_start] + new_tennis + s[old_tennis_end:]

# grandstand: center from the user's points, narrower stand
old_g = """    const gx = -133.5, gz = 61.5;
    const g = new THREE.Group(); g.position.set(gx, 0, gz); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);
    for (let i = 0; i < 6; i++) {
      const h = .42 * (i + 1);
      lmBox(31, h, 1.25, i % 2 ? LMAT.seat : LMAT.concrete, 0, h / 2, -3.6 + i * 1.25, g);
    }
    for (const x of [-15, 15]) for (const z of [-3.7, 3.7]) lmCyl(.17, .2, 5.7, 8, LMAT.metal, x, 2.85, z, g);
    lmBox(33, .3, 8.2, LMAT.white, 0, 5.85, 0, g);
    lmBox(32, .18, 1.0, LMAT.concreteDark, 0, .1, -4.25, g);
    addFeature({ kind: '看台', name: '主席台（南看台）', x: gx, z: gz, y: 7, angle: 79.7, layer: G.landmarks });"""
new_g = """    const gx = -115.04, gz = 60.68;
    const g = new THREE.Group(); g.position.set(gx, 0, gz); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);
    for (let i = 0; i < 6; i++) {
      const h = .42 * (i + 1);
      lmBox(18, h, 1.25, i % 2 ? LMAT.seat : LMAT.concrete, 0, h / 2, -3.6 + i * 1.25, g);
    }
    for (const x of [-8.2, 8.2]) for (const z of [-3.7, 3.7]) lmCyl(.17, .2, 5.7, 8, LMAT.metal, x, 2.85, z, g);
    lmBox(19.5, .3, 8.2, LMAT.white, 0, 5.85, 0, g);
    lmBox(18.5, .18, 1.0, LMAT.concreteDark, 0, .1, -4.25, g);
    addFeature({ kind: '看台', name: '主席台（南看台）', x: gx, z: gz, y: 7, angle: 79.7, layer: G.landmarks });"""
if old_g not in s: raise SystemExit('grandstand block missing')
s = s.replace(old_g, new_g)

# platform: center/length from user's two vertices
old_p = """    const px = -77, pz = -35;
    const g = new THREE.Group(); g.position.set(px, 0, pz); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);
    lmBox(8, 1.15, 28, LMAT.concrete, 0, .58, 0, g);
    for (const x of [-3.2, 3.2]) for (const z of [-11.5, 0, 11.5]) lmCyl(.17, .2, 6.0, 8, LMAT.metal, x, 3.0, z, g);
    const roof = new THREE.Mesh(new THREE.SphereGeometry(1, 30, 14, 0, Math.PI * 2, 0, Math.PI / 2), LMAT.white);
    roof.scale.set(5.2, 1.4, 14.5); roof.position.set(0, 6.1, 0); g.add(lmAdd(roof));
    lmBox(12, .25, 28.5, LMAT.white, 0, 6.05, 0, g);
    addFeature({ kind: '平台', name: '台下平台 · 膜结构', x: px, z: pz, y: 8, angle: CAMPUS_BEARING, layer: G.landmarks });"""
new_p = """    const px = -79.06, pz = -38.45;
    const g = new THREE.Group(); g.position.set(px, 0, pz); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);
    lmBox(8, 1.15, 36.05, LMAT.concrete, 0, .58, 0, g);
    for (const x of [-3.2, 3.2]) for (const z of [-17, 0, 17]) lmCyl(.17, .2, 6.0, 8, LMAT.metal, x, 3.0, z, g);
    const roof = new THREE.Mesh(new THREE.SphereGeometry(1, 30, 14, 0, Math.PI * 2, 0, Math.PI / 2), LMAT.white);
    roof.scale.set(5.2, 1.4, 18.5); roof.position.set(0, 6.1, 0); g.add(lmAdd(roof));
    lmBox(12, .25, 36.5, LMAT.white, 0, 6.05, 0, g);
    addFeature({ kind: '平台', name: '台下平台 · 膜结构', x: px, z: pz, y: 8, angle: CAMPUS_BEARING, layer: G.landmarks });"""
if old_p not in s: raise SystemExit('platform block missing')
s = s.replace(old_p, new_p)

# fountain center
s = s.replace("    const fx = 160, fz = -128;", "    const fx = 105.93, fz = -70.41;")

# yellow circular plaza + feature #32 (draw under gate/fountain)
insert_before = "  // 30: fountain inside the southeast gate"
plaza = r'''  // 32: the yellow-grid circular plaza in the entrance area
  const plazaX = 130.5, plazaZ = -80.03, plazaR = 39.1;
  (() => {
    const disc = new THREE.Mesh(new THREE.CircleGeometry(plazaR, 80), LMAT.plaza);
    disc.rotation.x = -Math.PI / 2; disc.position.set(plazaX, .036, plazaZ);
    G.landmarks.add(lmAdd(disc, false, true));
    const ring = new THREE.Mesh(new THREE.RingGeometry(plazaR - .7, plazaR, 80), LMAT.concreteDark);
    ring.rotation.x = -Math.PI / 2; ring.position.set(plazaX, .042, plazaZ);
    G.landmarks.add(lmAdd(ring, false, true));
    addFeature({ kind: '广场', name: '黄色网格广场', x: plazaX, z: plazaZ, y: 2, angle: 0, layer: G.landmarks });
  })();

'''
if insert_before not in s: raise SystemExit('fountain anchor missing')
s = s.replace(insert_before, plaza + insert_before)

p.write_text(s, encoding='utf-8')
print('user coordinates applied')
