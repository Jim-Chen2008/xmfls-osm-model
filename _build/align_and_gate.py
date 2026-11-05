from pathlib import Path
p = Path(r'xmfls-osm-model\src\app.js')
s = p.read_text(encoding='utf-8')

# campus local axis (from the OSM track's long sides: ~169.7 deg bearing / +10.3 deg Y rotation)
s = s.replace("  const FEATURES = [];\n  const FEATURE_BY_REC = new Map();",
              "  const CAMPUS_ROT = THREE.MathUtils.degToRad(10.3);\n  const CAMPUS_BEARING = 169.7;\n  const FEATURES = [];\n  const FEATURE_BY_REC = new Map();")

# extra materials + gate stone/sign texture helpers
anchor = "  function lmAdd(mesh, cast = true, receive = true) {"
helper = r'''  function makeStoneTexture() {
    const c = document.createElement('canvas'); c.width = 512; c.height = 512;
    const x = c.getContext('2d');
    x.fillStyle = '#cdc5b4'; x.fillRect(0, 0, 512, 512);
    const rows = 6, cols = 4, rh = 512 / rows;
    for (let r = 0; r < rows; r++) {
      const off = r % 2 ? 64 : 0;
      for (let col = -1; col < cols + 1; col++) {
        const x0 = col * 128 + off, y0 = r * rh;
        const shade = 194 + ((r * 13 + col * 7) % 18);
        x.fillStyle = 'rgb(' + shade + ',' + (shade - 7) + ',' + (shade - 19) + ')';
        x.fillRect(x0 + 2, y0 + 2, 124, rh - 4);
        x.strokeStyle = 'rgba(112,104,90,.34)'; x.lineWidth = 2;
        x.strokeRect(x0 + 1, y0 + 1, 126, rh - 2);
      }
    }
    for (let i = 0; i < 900; i++) {
      x.fillStyle = 'rgba(80,74,63,' + (Math.random() * .045) + ')';
      x.fillRect(Math.random() * 512, Math.random() * 512, 1, 1);
    }
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(5, 2); t.anisotropy = 4;
    return t;
  }
  LMAT.gateStone = new THREE.MeshStandardMaterial({ map: makeStoneTexture(), roughness: .9, metalness: .01 });
  function gateSignTexture() {
    const c = document.createElement('canvas'); c.width = 2048; c.height = 512;
    const x = c.getContext('2d');
    x.clearRect(0, 0, 2048, 512);
    x.textAlign = 'center'; x.textBaseline = 'middle';
    x.fillStyle = '#b08a42';
    x.font = '600 150px "STKaiti","KaiTi","Microsoft YaHei",serif';
    x.fillText('厦门外国语学校', 1024, 175);
    x.font = '500 48px "Times New Roman",serif';
    x.fillStyle = '#a8833f';
    x.fillText('XIAMEN FOREIGN LANGUAGE SCHOOL', 1024, 355);
    const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; t.anisotropy = 8;
    return t;
  }
  const gateSignMat = new THREE.MeshBasicMaterial({ map: gateSignTexture(), transparent: true, side: THREE.DoubleSide });

'''
if anchor not in s: raise SystemExit('lmAdd anchor missing')
s = s.replace(anchor, helper + anchor)

# track/field angles
s = s.replace("addFeature({ kind: '场地', name: '田径场', x: outerC[0], z: outerC[1] + 23, y: 2.4, angle: 0, layer: G.sports });",
              "addFeature({ kind: '场地', name: '田径场', x: outerC[0], z: outerC[1] + 23, y: 2.4, angle: CAMPUS_BEARING, layer: G.sports });")
s = s.replace("addFeature({ kind: '场地', name: '足球场', x: innerC[0], z: innerC[1] - 21, y: 2.4, angle: 0, layer: G.sports });",
              "addFeature({ kind: '场地', name: '足球场', x: innerC[0], z: innerC[1] - 21, y: 2.4, angle: CAMPUS_BEARING, layer: G.sports });")

# basketball block -> one rotated group
start = s.index('  // 24: the six basketball courts')
end = s.index('  // 25–26: two tennis courts', start)
bball = r'''  // 24: six basketball courts, aligned to the track axis
  const bball = (DATA.pitches || []).find(p => p.id === '638483883');
  if (bball) {
    const x0 = -73, x1 = -19, z0 = -94, z1 = -1;
    const bcx = (x0 + x1) / 2, bcz = (z0 + z1) / 2;
    const g = new THREE.Group(); g.position.set(bcx, 0, bcz); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);
    lmRect(x1 - x0 + 4, z1 - z0 + 4, LMAT.courtRed, 0, 0, .058, g);
    const cols = 2, rows = 3;
    const cw = (x1 - x0) / cols, cd = (z1 - z0) / rows;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cx = (c + .5) * cw - (x1 - x0) / 2;
        const cz = (r + .5) * cd - (z1 - z0) / 2;
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
    addFeature({ kind: '球场', name: '篮球场 ×6', x: bcx, z: bcz, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });
  } else {
    addFeature({ kind: '球场', name: '篮球场 ×6', x: -46, z: -47.5, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });
  }

'''
s = s[:start] + bball + s[end:]

# tennis block -> rotated per-court groups
start = s.index('  // 25–26: two tennis courts')
end = s.index('  // 27: covered grandstand', start)
tennis = r'''  // 25–26: two tennis courts west of the gym, aligned to the track axis
  const tennisDefs = [
    { name: '网球场 A', x: -173, z: 92 },
    { name: '网球场 B', x: -173, z: 128 }
  ];
  for (const tf of tennisDefs) {
    const cw = 18, cd = 30;
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
s = s[:start] + tennis + s[end:]

# grandstand and platform: rotate to campus axis + correct index angle
s = s.replace("    const g = new THREE.Group(); g.position.set(gx, 0, gz); G.landmarks.add(g);",
              "    const g = new THREE.Group(); g.position.set(gx, 0, gz); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);")
s = s.replace("    addFeature({ kind: '看台', name: '主席台（南看台）', x: gx, z: gz, y: 7, angle: 90, layer: G.landmarks });",
              "    addFeature({ kind: '看台', name: '主席台（南看台）', x: gx, z: gz, y: 7, angle: 79.7, layer: G.landmarks });")
s = s.replace("    const g = new THREE.Group(); g.position.set(px, 0, pz); G.landmarks.add(g);",
              "    const g = new THREE.Group(); g.position.set(px, 0, pz); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);")
s = s.replace("    addFeature({ kind: '平台', name: '台下平台 · 膜结构', x: px, z: pz, y: 8, angle: 0, layer: G.landmarks });",
              "    addFeature({ kind: '平台', name: '台下平台 · 膜结构', x: px, z: pz, y: 8, angle: CAMPUS_BEARING, layer: G.landmarks });")

# replace gate section with the user's 154,-95 -> 118,-125 stone gate
start = s.index('  // gate: intersection of the 1189318108')
end = s.index('  // 30: fountain inside the southeast gate', start)
gate = r'''  // 29: the real stone main gate, on the user-supplied line (154,-95) -> (118,-125)
  const gateA = [154, -95], gateB = [118, -125];
  const gateX = (gateA[0] + gateB[0]) / 2, gateZ = (gateA[1] + gateB[1]) / 2;
  const gateDx = gateB[0] - gateA[0], gateDz = gateB[1] - gateA[1];
  const gateLen = Math.hypot(gateDx, gateDz);
  const gateRot = Math.atan2(gateDx, gateDz);
  const gateBearing = ((Math.atan2(gateDx, -gateDz) * 180 / Math.PI) % 180 + 180) % 180;
  (() => {
    const g = new THREE.Group();
    g.position.set(gateX, 0, gateZ);
    g.rotation.y = gateRot;
    G.landmarks.add(g);
    const L = gateLen, T = 3.2, H = 9.4, open = 10, sideOpen = 3.2, sideY = 3.6;
    const hz = L / 2;
    const doorL = 14.6;
    function wallPiece(z0, z1, y0, y1, mat = LMAT.gateStone) {
      if (z1 - z0 < .01 || y1 - y0 < .01) return;
      lmBox(T, y1 - y0, z1 - z0, mat, 0, (y0 + y1) / 2, (z0 + z1) / 2, g);
    }
    // central opening + two side pedestrian openings
    wallPiece(-hz, -doorL - sideOpen / 2, 0, H);
    wallPiece(-doorL + sideOpen / 2, -open / 2, 0, H);
    wallPiece(-open / 2, open / 2, 6.4, H);
    wallPiece(open / 2, doorL - sideOpen / 2, 0, H);
    wallPiece(doorL + sideOpen / 2, hz, 0, H);
    for (const zc of [-doorL, doorL]) {
      wallPiece(zc - sideOpen / 2, zc + sideOpen / 2, sideY, H);
    }
    // plinth + coping + central pilasters/lintel
    lmBox(T + .5, .5, L + .4, LMAT.concreteDark, 0, .25, 0, g);
    lmBox(T + .5, .45, L + .4, LMAT.concrete, 0, H + .22, 0, g);
    for (const s of [-1, 1]) {
      lmBox(T + .45, H, 1.15, LMAT.gateStone, 0, H / 2, s * (open / 2 + .55), g);
      lmBox(T + .35, 1.1, 1.5, LMAT.concrete, 0, H - .5, s * (open / 2 + .65), g);
    }
    lmBox(T + .35, .55, open + 2.0, LMAT.concrete, 0, 6.65, 0, g);
    // anti-climb spikes on the coping
    for (let i = 0; i < 58; i++) {
      const z = -hz + .5 + i * (L - 1) / 57;
      lmCyl(.035, .045, 1.05, 5, LMAT.metal, 0, H + .95, z, g);
    }
    // gold school name on both faces
    for (const s of [-1, 1]) {
      const sign = new THREE.Mesh(new THREE.PlaneGeometry(Math.min(34, L - 5), 3.3), gateSignMat);
      sign.position.set(s * (T / 2 + .02), 7.8, 0);
      sign.rotation.y = s > 0 ? Math.PI / 2 : -Math.PI / 2;
      g.add(sign);
    }
    // metal sliding gate and pedestrian leaves
    for (let i = 0; i < 19; i++) {
      const z = -open / 2 + .25 + i * (open - .5) / 18;
      lmCyl(.045, .045, 4.7, 5, LMAT.metal, 0, 2.35, z, g);
    }
    for (const y of [.35, 1.55, 2.75, 4.25]) lmBox(.08, .06, open - .3, LMAT.metal, 0, y, 0, g);
    for (const zc of [-doorL, doorL]) {
      for (let i = 0; i < 5; i++) lmCyl(.035, .035, 2.9, 5, LMAT.metal, 0, 1.45, zc - 1.2 + i * .6, g);
      lmBox(.06, .05, sideOpen, LMAT.metal, 0, 2.2, zc, g);
    }
    addFeature({ kind: '大门', name: '大门', x: gateX, z: gateZ, y: 12, angle: Math.round(gateBearing * 10) / 10, layer: G.landmarks });
  })();

  // user's gate reference line, kept in the guide layer
  {
    const gm = new THREE.LineDashedMaterial({ color: 0xb45b3e, transparent: true, opacity: .55, dashSize: 3, gapSize: 2 });
    const gl = new THREE.Line(new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(gateA[0], .32, gateA[1]), new THREE.Vector3(gateB[0], .32, gateB[1])
    ]), gm);
    gl.computeLineDistances(); G.guide.add(gl);
  }

'''
s = s[:start] + gate + s[end:]

# move fountain near the new gate / plaza, keep its circular geometry
s = s.replace("    const fx = 185, fz = -28;", "    const fx = 160, fz = -128;")

p.write_text(s, encoding='utf-8')
print('aligned features and rebuilt gate')
