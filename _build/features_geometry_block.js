  /* ================= OSM + real-scene landmarks ================= */
  G.landmarks = new THREE.Group();
  G.guide = new THREE.Group();
  scene.add(G.landmarks, G.guide);

  const LMAT = {
    concrete: new THREE.MeshStandardMaterial({ color: 0xcfc3b0, roughness: .95, metalness: 0 }),
    concreteDark: new THREE.MeshStandardMaterial({ color: 0x8b8171, roughness: .96, metalness: 0 }),
    white: new THREE.MeshStandardMaterial({ color: 0xf3eee2, roughness: .86, metalness: .01, side: THREE.DoubleSide }),
    tile: new THREE.MeshStandardMaterial({ color: 0xe5ded0, roughness: .9, metalness: .01 }),
    seat: new THREE.MeshStandardMaterial({ color: 0xb9a98f, roughness: .92 }),
    metal: new THREE.MeshStandardMaterial({ color: 0x6e7871, roughness: .48, metalness: .55 }),
    water: new THREE.MeshStandardMaterial({ color: 0x4b7e85, roughness: .18, metalness: .12, transparent: true, opacity: .88 }),
    waterDeep: new THREE.MeshStandardMaterial({ color: 0x315e66, roughness: .25, metalness: .08 }),
    courtRed: new THREE.MeshStandardMaterial({ color: 0xa75b48, roughness: .96 }),
    courtGreen: new THREE.MeshStandardMaterial({ color: 0x567354, roughness: .96 }),
    tennis: new THREE.MeshStandardMaterial({ color: 0x5e7f68, roughness: .96 }),
    tennisBlue: new THREE.MeshStandardMaterial({ color: 0x527b84, roughness: .95 }),
    line: new THREE.LineBasicMaterial({ color: 0xf4efe1, transparent: true, opacity: .8 }),
    net: new THREE.MeshBasicMaterial({ color: 0xe9e5d9, transparent: true, opacity: .32, side: THREE.DoubleSide })
  };

  function lmAdd(mesh, cast = true, receive = true) {
    mesh.castShadow = cast; mesh.receiveShadow = receive;
    return mesh;
  }
  function lmBox(w, h, d, material, x, y, z, parent = G.landmarks, ry = 0) {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
    m.position.set(x, y, z); m.rotation.y = ry;
    parent.add(lmAdd(m)); return m;
  }
  function lmCyl(rt, rb, h, seg, material, x, y, z, parent = G.landmarks) {
    const m = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg), material);
    m.position.set(x, y, z); parent.add(lmAdd(m)); return m;
  }
  function lmRect(w, d, material, x, z, y, parent = G.landmarks, ry = 0) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), material);
    m.rotation.x = -Math.PI / 2; m.rotation.z = ry;
    m.position.set(x, y, z); parent.add(lmAdd(m, false, true)); return m;
  }
  function lmLine(points, y, material, parent = G.guide) {
    const geo = new THREE.BufferGeometry().setFromPoints(points.map(p => new THREE.Vector3(p[0], y, p[1])));
    const m = new THREE.Line(geo, material); parent.add(m); return m;
  }
  function lmTextPlane(text, w, h) {
    const cv = document.createElement('canvas'); cv.width = 1024; cv.height = 256;
    const c = cv.getContext('2d');
    c.clearRect(0, 0, 1024, 256);
    c.textAlign = 'center'; c.textBaseline = 'middle';
    let size = 112;
    c.font = '600 ' + size + 'px "Microsoft YaHei","Noto Sans SC",sans-serif';
    while (c.measureText(text).width > 940 && size > 32) {
      size -= 4; c.font = '600 ' + size + 'px "Microsoft YaHei","Noto Sans SC",sans-serif';
    }
    c.fillStyle = '#9b7438';
    c.fillText(text, 512, 128);
    const tex = new THREE.CanvasTexture(cv); tex.encoding = THREE.sRGBEncoding; tex.anisotropy = 4;
    return new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.DoubleSide }));
  }
  function polygonBearing(poly) {
    let best = 0, bestL = 0;
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length];
      const dx = b[0] - a[0], dz = b[1] - a[1];
      const L = Math.hypot(dx, dz);
      if (L > bestL) { bestL = L; best = Math.atan2(dx, -dz) * 180 / Math.PI; }
    }
    return Math.round((((best % 180) + 180) % 180) * 10) / 10;
  }
  function padNo(n) { return String(n).padStart(2, '0'); }

  const FEATURES = [];
  const FEATURE_BY_REC = new Map();
  function addFeature(f) {
    f.no = FEATURES.length + 1;
    f.label = padNo(f.no);
    if (f.rec) { f.rec._featureNo = f.no; f.rec._angle = f.angle; FEATURE_BY_REC.set(f.rec, f); }
    FEATURES.push(f);
    return f;
  }

  // 01–21: OSM building footprints
  for (const b of DATA.buildings) {
    addFeature({
      kind: '建筑',
      name: b.name || ('OSM 建筑 ' + b.id),
      short: b.name || ('建筑 ' + b.id),
      x: b.centroid[0], z: b.centroid[1],
      y: height + 2.5,
      angle: polygonBearing(b.polygon),
      rec: b,
      layer: b.inside ? G.inside : G.outside
    });
  }

  // 22–23: track and football field
  const innerC = DATA.track && DATA.track.inner ? DATA.track.inner.centroid : [0, 0];
  const outerC = DATA.track && DATA.track.outer ? DATA.track.outer.centroid : [0, 0];
  addFeature({ kind: '场地', name: '田径场', x: outerC[0], z: outerC[1] + 23, y: 2.4, angle: 0, layer: G.sports });
  addFeature({ kind: '场地', name: '足球场', x: innerC[0], z: innerC[1] - 21, y: 2.4, angle: 0, layer: G.sports });

  // 24: the six basketball courts over the OSM pitch footprint
  const bball = (DATA.pitches || []).find(p => p.id === '638483883');
  if (bball) {
    const [x0, x1, z0, z1] = bball.bbox;
    lmAdd(flatPolygon(bball.polygon, .062, LMAT.courtRed), false, true);
    const cols = 2, rows = 3;
    const cw = (x1 - x0) / cols, cd = (z1 - z0) / rows;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cx = x0 + (c + .5) * cw;
        const cz = z0 + (r + .5) * cd;
        const cwid = Math.min(21, cw - 4.5), cdepth = Math.min(25, cd - 4.5);
        lmRect(cwid, cdepth, LMAT.courtGreen, cx, cz, .072, G.landmarks);
        // court outline and centre line, kept in OSM/real-scene scale
        const pts = [[cx - cwid / 2, cz - cdepth / 2], [cx + cwid / 2, cz - cdepth / 2], [cx + cwid / 2, cz + cdepth / 2], [cx - cwid / 2, cz + cdepth / 2]];
        const loop = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts.map(p => new THREE.Vector3(p[0], .077, p[1]))), LMAT.line);
        G.landmarks.add(loop);
        const mid = new THREE.Line(new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(cx, .078, cz - cdepth / 2), new THREE.Vector3(cx, .078, cz + cdepth / 2)
        ]), LMAT.line);
        G.landmarks.add(mid);
        // two hoops per court
        for (const s of [-1, 1]) {
          const zEnd = cz + s * (cdepth / 2 + 1.1);
          lmCyl(.12, .15, 3.15, 8, LMAT.metal, cx, 1.58, zEnd);
          lmBox(1.75, 1.05, .1, LMAT.white, cx, 3.15, zEnd + s * .1, G.landmarks);
          const rim = new THREE.Mesh(new THREE.TorusGeometry(.4, .035, 6, 18), LMAT.metal);
          rim.rotation.x = Math.PI / 2; rim.position.set(cx, 2.72, zEnd - s * .25);
          G.landmarks.add(lmAdd(rim));
        }
      }
    }
    addFeature({ kind: '球场', name: '篮球场 ×6', x: (x0 + x1) / 2, z: (z0 + z1) / 2, y: 3.5, angle: 0, layer: G.landmarks });
  } else {
    addFeature({ kind: '球场', name: '篮球场 ×6', x: -57.8, z: -53.7, y: 3.5, angle: 0, layer: G.landmarks });
  }

  // 25–26: two tennis courts west of the gym
  const tennisY = .07;
  const tennisDefs = [
    { no: 0, name: '网球场 A', x: -173, z: 92 },
    { no: 0, name: '网球场 B', x: -173, z: 128 }
  ];
  for (const tf of tennisDefs) {
    const cw = 18, cd = 30;
    lmRect(cw + 3, cd + 3, LMAT.courtRed, tf.x, tf.z, .058);
    lmRect(cw, cd, LMAT.tennis, tf.x, tf.z, .066);
    const pts = [[tf.x - cw / 2, tf.z - cd / 2], [tf.x + cw / 2, tf.z - cd / 2], [tf.x + cw / 2, tf.z + cd / 2], [tf.x - cw / 2, tf.z + cd / 2]];
    G.landmarks.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts.map(p => new THREE.Vector3(p[0], .073, p[1]))), LMAT.line));
    // net
    const net = new THREE.Mesh(new THREE.PlaneGeometry(cw - 1, .82), LMAT.net);
    net.position.set(tf.x, 1.1, tf.z); G.landmarks.add(lmAdd(net, false, false));
    for (const s of [-1, 1]) lmCyl(.08, .1, 1.3, 6, LMAT.metal, tf.x + s * (cw / 2 - .5), .65, tf.z);
    lmLine([[tf.x, tf.z - cd / 2], [tf.x, tf.z + cd / 2]], .074, LMAT.line, G.landmarks);
    addFeature({ kind: '球场', name: tf.name, x: tf.x, z: tf.z, y: 3.5, angle: 0, layer: G.landmarks });
  }

  // 27: covered grandstand south of the track
  (() => {
    const gx = -133.5, gz = 61.5;
    const g = new THREE.Group(); g.position.set(gx, 0, gz); G.landmarks.add(g);
    for (let i = 0; i < 6; i++) {
      const h = .42 * (i + 1);
      lmBox(31, h, 1.25, i % 2 ? LMAT.seat : LMAT.concrete, 0, h / 2, -3.6 + i * 1.25, g);
    }
    for (const x of [-15, 15]) for (const z of [-3.7, 3.7]) lmCyl(.17, .2, 5.7, 8, LMAT.metal, x, 2.85, z, g);
    lmBox(33, .3, 8.2, LMAT.white, 0, 5.85, 0, g);
    lmBox(32, .18, 1.0, LMAT.concreteDark, 0, .1, -4.25, g);
    addFeature({ kind: '看台', name: '主席台（南看台）', x: gx, z: gz, y: 7, angle: 90, layer: G.landmarks });
  })();

  // 28: platform + membrane canopy on the east edge of the track
  (() => {
    const px = -68.5, pz = -35;
    const g = new THREE.Group(); g.position.set(px, 0, pz); G.landmarks.add(g);
    lmBox(10, 1.15, 28, LMAT.concrete, 0, .58, 0, g);
    for (const x of [-4.1, 4.1]) for (const z of [-12, 0, 12]) lmCyl(.17, .2, 6.2, 8, LMAT.metal, x, 3.1, z, g);
    const roof = new THREE.Mesh(new THREE.SphereGeometry(1, 30, 14, 0, Math.PI * 2, 0, Math.PI / 2), LMAT.white);
    roof.scale.set(6.2, 1.45, 15); roof.position.set(0, 6.3, 0); g.add(lmAdd(roof));
    lmBox(10.5, .25, 28.5, LMAT.white, 0, 6.25, 0, g);
    addFeature({ kind: '平台', name: '台下平台 · 膜结构', x: px, z: pz, y: 8, angle: 0, layer: G.landmarks });
  })();

  // gate: intersection of the 1189318108 — 1189318114 axis with the school boundary
  const f1 = DATA.buildings.find(b => b.id === '1189318108');
  const f7 = DATA.buildings.find(b => b.id === '1189318114');
  let gateX = 190.9, gateZ = -47.7, gateAngle = 173.3;
  if (f1 && f7) {
    const a = f1.centroid, b = f7.centroid;
    const dx = b[0] - a[0], dz = b[1] - a[1];
    let hit = null;
    const poly = DATA.school.polygon;
    for (let i = 0; i < poly.length; i++) {
      const p = poly[i], q = poly[(i + 1) % poly.length];
      const ex = q[0] - p[0], ez = q[1] - p[1];
      const den = dx * ez - dz * ex;
      if (Math.abs(den) < 1e-9) continue;
      const t = ((p[0] - b[0]) * ez - (p[1] - b[1]) * ex) / den;
      const u = ((p[0] - b[0]) * dz - (p[1] - b[1]) * dx) / den;
      if (t > 0 && u >= -.001 && u <= 1.001) {
        const hp = [b[0] + t * dx, b[1] + t * dz];
        if (!hit || t < hit.t) hit = { t, p: hp, a: p, b: q };
      }
    }
    if (hit) {
      gateX = hit.p[0]; gateZ = hit.p[1];
      const bx = hit.b[0] - hit.a[0], bz = hit.b[1] - hit.a[1];
      gateAngle = ((Math.atan2(bx, -bz) * 180 / Math.PI) % 180 + 180) % 180;
    }
    // debug / verification line: 01 -> 07 -> gate
    const lineMat = new THREE.LineDashedMaterial({ color: 0xb45b3e, transparent: true, opacity: .62, dashSize: 4, gapSize: 3 });
    const axis = new THREE.Line(new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(a[0], .22, a[1]), new THREE.Vector3(b[0], .22, b[1]), new THREE.Vector3(gateX, .22, gateZ)
    ]), lineMat);
    axis.computeLineDistances(); G.guide.add(axis);
  }

  (() => {
    const g = new THREE.Group();
    g.position.set(gateX, 0, gateZ);
    g.rotation.y = Math.atan2(Math.sin(gateAngle * Math.PI / 180), -Math.cos(gateAngle * Math.PI / 180));
    G.landmarks.add(g);
    const wallL = 24, open = 8, th = 2.4, H = 8.2;
    const side = (wallL - open) / 2;
    for (const s of [-1, 1]) {
      lmBox(th, H, side, LMAT.tile, 0, H / 2, s * (open / 2 + side / 2), g);
    }
    lmBox(th, H - 6.5, open, LMAT.tile, 0, 6.5 + (H - 6.5) / 2, 0, g);
    lmBox(th + .4, .4, wallL + .3, LMAT.concrete, 0, H + .18, 0, g);
    // silver gate leaves folded to the sides (visual only)
    for (const s of [-1, 1]) {
      for (let i = 0; i < 6; i++) lmCyl(.035, .035, 2.2, 5, LMAT.metal, -1.15, 1.1, s * (open / 2 - .25 - i * .3), g);
    }
    // name on both faces
    const sign = lmTextPlane(DATA.school.name || '厦门外国语学校', 13, 2.0);
    for (const s of [-1, 1]) {
      const sm = sign.clone();
      sm.position.set(s * 1.24, 6.8, 0);
      sm.rotation.y = s > 0 ? Math.PI / 2 : -Math.PI / 2;
      g.add(sm);
    }
    addFeature({ kind: '大门', name: '大门', x: gateX, z: gateZ, y: 11, angle: Math.round(gateAngle * 10) / 10, layer: G.landmarks });
  })();

  // 30: fountain inside the southeast gate
  (() => {
    const fx = 185, fz = -28;
    const g = new THREE.Group(); g.position.set(fx, 0, fz); G.landmarks.add(g);
    lmCyl(10.5, 10.5, .16, 48, LMAT.concrete, 0, .08, 0, g);
    lmCyl(6.2, 6.5, .55, 40, LMAT.concreteDark, 0, .3, 0, g);
    lmCyl(5.8, 5.8, .18, 40, LMAT.waterDeep, 0, .58, 0, g);
    lmCyl(5.5, 5.5, .12, 40, LMAT.water, 0, .69, 0, g);
    lmCyl(2.4, 2.8, .55, 32, LMAT.concrete, 0, .45, 0, g);
    lmCyl(1.2, 1.4, 1.4, 20, LMAT.concreteDark, 0, .95, 0, g);
    for (let i = 0; i < 8; i++) {
      const a = i / 8 * Math.PI * 2;
      lmCyl(.04, .05, .8, 5, LMAT.water, Math.cos(a) * 3.6, 1.0, Math.sin(a) * 3.6, g);
    }
    addFeature({ kind: '喷泉', name: '喷泉', x: fx, z: fz, y: 4, angle: 0, layer: G.landmarks });
  })();

  // 31: school boundary (annotation, no extra geometry)
  addFeature({ kind: '边界', name: '校园边界', x: 0, z: -153, y: 2, angle: 0, layer: G.ground });
