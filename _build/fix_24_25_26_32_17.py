from pathlib import Path
p = Path(r'xmfls-osm-model\src\app.js')
s = p.read_text(encoding='utf-8')

# extra volleyball material
s = s.replace("  LMAT.plaza = new THREE.MeshStandardMaterial({ map: makeYellowGridTexture(), roughness: .92, metalness: .01 });",
              "  LMAT.plaza = new THREE.MeshStandardMaterial({ map: makeYellowGridTexture(), roughness: .92, metalness: .01 });\n  LMAT.volley = new THREE.MeshStandardMaterial({ color: 0x6c8b8c, roughness: .95, metalness: 0 });")

# move the gym (way 638485974) 4 m east so it sits against the tennis block
gym_anchor = "  // 22–23: track and football field"
gym_shift = r'''  // the user's tennis block touches the gym: shift the gym (OSM way 638485974) east
  const GYM_SHIFT_X = 4;
  {
    const gymView = buildingViews.find(v => v.rec.id === '638485974');
    if (gymView) {
      gymView.group.position.x += GYM_SHIFT_X;
      gymView.rec.centroid[0] += GYM_SHIFT_X;
      const gf = FEATURE_BY_REC.get(gymView.rec);
      if (gf) gf.x += GYM_SHIFT_X;
    }
  }

'''
if gym_anchor not in s: raise SystemExit('gym anchor missing')
s = s.replace(gym_anchor, gym_shift + gym_anchor)

# rewrite basketball block (4 basketball + 3 volleyball)
start = s.index('  // 24: six basketball courts')
end = s.index('  // 25–26: two tennis courts', start)
new_bball = r'''  // 24: four basketball courts + three volleyball courts on the top row
  const bball = (DATA.pitches || []).find(p => p.id === '638483883');
  if (bball) {
    const x0 = -73, x1 = -19, z0 = -94, z1 = -1;
    const bcx = (x0 + x1) / 2, bcz = (z0 + z1) / 2;
    const bw = x1 - x0, bd = z1 - z0;
    const g = new THREE.Group(); g.position.set(bcx, 0, bcz); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);
    lmRect(bw + 4, bd + 4, LMAT.courtRed, 0, 0, .058, g);
    const rows = 3, cols = 2;
    const cd = bd / rows, cw = bw / cols;
    // lower two rows: basketball
    for (let r = 1; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cx = (c + .5) * cw - bw / 2;
        const cz = (r + .5) * cd - bd / 2;
        const cwid = Math.min(21, cw - 4.5), cdepth = Math.min(25, cd - 4.5);
        lmRect(cwid, cdepth, LMAT.courtGreen, cx, cz, .072, g);
        const pts = [[cx - cwid / 2, cz - cdepth / 2], [cx + cwid / 2, cz - cdepth / 2], [cx + cwid / 2, cz + cdepth / 2], [cx - cwid / 2, cz + cdepth / 2]];
        g.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts.map(p => new THREE.Vector3(p[0], .077, p[1]))), LMAT.line));
        g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(cx, .078, cz - cdepth / 2), new THREE.Vector3(cx, .078, cz + cdepth / 2)
        ]), LMAT.line));
        for (const s of [-1, 1]) {
          const zEnd = cz + s * (cdepth / 2 + 1.1);
          lmCyl(.12, .15, 3.15, 8, LMAT.metal, cx, 1.58, zEnd, g);
          lmBox(1.75, 1.05, .1, LMAT.white, cx, 3.15, zEnd + s * .1, g);
          const rim = new THREE.Mesh(new THREE.TorusGeometry(.4, .035, 6, 18), LMAT.metal);
          rim.rotation.x = Math.PI / 2; rim.position.set(cx, 2.72, zEnd - s * .25);
          g.add(lmAdd(rim));
        }
      }
    }
    // top row: three volleyball courts
    for (let c = 0; c < 3; c++) {
      const cx = (c + .5) * (bw / 3) - bw / 2;
      const cz = .5 * cd - bd / 2;
      const cwid = bw / 3 - 4, cdepth = cd - 6;
      lmRect(cwid, cdepth, LMAT.volley, cx, cz, .072, g);
      const pts = [[cx - cwid / 2, cz - cdepth / 2], [cx + cwid / 2, cz - cdepth / 2], [cx + cwid / 2, cz + cdepth / 2], [cx - cwid / 2, cz + cdepth / 2]];
      g.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts.map(p => new THREE.Vector3(p[0], .077, p[1]))), LMAT.line));
      // net across x at the middle of the court
      const net = new THREE.Mesh(new THREE.PlaneGeometry(cwid - 1, .8), LMAT.net);
      net.position.set(cx, 1.18, cz); g.add(lmAdd(net, false, false));
      for (const s of [-1, 1]) lmCyl(.06, .08, 2.15, 6, LMAT.metal, cx + s * (cwid / 2 - .4), 1.08, cz, g);
      g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(cx, .078, cz - cdepth / 2), new THREE.Vector3(cx, .078, cz + cdepth / 2)
      ]), LMAT.line));
    }
    addFeature({ kind: '球场', name: '篮球场 ×4 / 排球场 ×3', x: bcx, z: bcz, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });
  } else {
    addFeature({ kind: '球场', name: '篮球场 ×4 / 排球场 ×3', x: -46, z: -47.5, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });
  }

'''
s = s[:start] + new_bball + s[end:]

# tennis: make the two courts head-to-tail, no gap, a+b = one rectangle
s = s.replace("    { name: '网球场 A', x: -156.11, z: 70.18 },\n    { name: '网球场 B', x: -156.11, z: 103.07 }", "    { name: '网球场 A', x: -156.11, z: 70.18 },\n    { name: '网球场 B', x: -156.11, z: 103.07 }")
s = s.replace("    const cw = 24, cd = 30;", "    const cw = 24, cd = 32.885;")

# yellow plaza becomes an ellipse (bounds of the three user points, with margin)
old_plaza = """  const plazaX = 130.5, plazaZ = -80.03, plazaR = 39.1;
  (() => {
    const disc = new THREE.Mesh(new THREE.CircleGeometry(plazaR, 80), LMAT.plaza);
    disc.rotation.x = -Math.PI / 2; disc.position.set(plazaX, .036, plazaZ);
    G.landmarks.add(lmAdd(disc, false, true));
    const ring = new THREE.Mesh(new THREE.RingGeometry(plazaR - .7, plazaR, 80), LMAT.concreteDark);
    ring.rotation.x = -Math.PI / 2; ring.position.set(plazaX, .042, plazaZ);
    G.landmarks.add(lmAdd(ring, false, true));
  })();"""
new_plaza = """  const plazaX = 121.365, plazaZ = -86.935, plazaRX = 26, plazaRZ = 34;
  (() => {
    const g = new THREE.Group(); g.position.set(plazaX, 0, plazaZ); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);
    const disc = new THREE.Mesh(new THREE.CircleGeometry(1, 96), LMAT.plaza);
    disc.rotation.x = -Math.PI / 2; disc.scale.set(plazaRX, plazaRZ, 1);
    g.add(lmAdd(disc, false, true));
    const ring = new THREE.Mesh(new THREE.RingGeometry(.97, 1, 96), LMAT.concreteDark);
    ring.rotation.x = -Math.PI / 2; ring.scale.set(plazaRX, plazaRZ, 1);
    g.add(lmAdd(ring, false, true));
  })();"""
if old_plaza not in s: raise SystemExit('plaza block missing')
s = s.replace(old_plaza, new_plaza)
s = s.replace("addFeature({ kind: '广场', name: '黄色网格广场', x: 130.5, z: -80.03, y: 2, angle: 0, layer: G.landmarks });",
              "addFeature({ kind: '广场', name: '黄色网格椭圆广场', x: 121.365, z: -86.935, y: 2, angle: CAMPUS_BEARING, layer: G.landmarks });")

p.write_text(s, encoding='utf-8')
print('24/25/26/32/17 updated')
