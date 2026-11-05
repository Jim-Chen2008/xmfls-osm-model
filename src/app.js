(() => {
  'use strict';

  const DATA = window.OSM_MODEL;
  if (!DATA || !DATA.school) {
    document.getElementById('loader').innerHTML = '<b>OSM 数据未加载</b>';
    return;
  }

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const fmt = (n, d = 0) => Number(n).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d });
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  const stage = $('#stage');
  const labelsEl = $('#labels');
  const tooltipEl = $('#tooltip');
  const loader = $('#loader');

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = .90;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.setAttribute('aria-label', 'OSM 校区体块模型，可拖拽旋转');
  stage.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0xebe5da, 1000, 3000);
  const camera = new THREE.PerspectiveCamera(40, window.innerWidth / window.innerHeight, .5, 5000);

  /* ---------- groups ---------- */
  const G = {
    ground: new THREE.Group(),
    landuse: new THREE.Group(),
    sports: new THREE.Group(),
    roads: new THREE.Group(),
    inside: new THREE.Group(),
    outside: new THREE.Group(),
    context: new THREE.Group(),
    grid: new THREE.Group()
  };
  Object.values(G).forEach(g => scene.add(g));

  const HEIGHT_DEFAULT = 15;
  let height = HEIGHT_DEFAULT;

  /* ---------- palette ---------- */
  const COL = {
    ground: 0xbdb19e,
    schoolGround: 0xd4c5ae,
    insideWall: 0xe4d7c3,
    insideTop: 0x6b6153,
    outsideWall: 0xa0a199,
    outsideTop: 0x666a61,
    edge: 0x41483f,
    edgeSoft: 0x6d746b,
    track: 0x8f3d2b,
    pitch: 0x496640,
    schoolLine: 0x3d5849,
    road: 0x777b72,
    context: 0x8e8d83,
    accent: 0xb56242,
    hover: 0xd19b5f
  };

  /* ---------- lights ---------- */
  const hemi = new THREE.HemisphereLight(0xfbf5e9, 0x555a4b, .27);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xfff2dc, 1.75);
  sun.position.set(-330, 400, 250);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.type = THREE.PCFSoftShadowMap;
  const sc = sun.shadow.camera;
  sc.left = -420; sc.right = 420; sc.top = 420; sc.bottom = -420; sc.near = 1; sc.far = 1500;
  sun.shadow.bias = -0.0003;
  sun.shadow.normalBias = .06;
  sc.updateProjectionMatrix();
  scene.add(sun, sun.target);
  const fill = new THREE.DirectionalLight(0xc9d7d1, .13);
  fill.position.set(-300, 220, -260);
  scene.add(fill);
  scene.add(new THREE.AmbientLight(0xf0e9dc, .06));

  /* ---------- ground ---------- */
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(5000, 5000),
    new THREE.MeshStandardMaterial({ color: COL.ground, roughness: 1, metalness: 0 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -.04;
  ground.receiveShadow = true;
  G.ground.add(ground);

  // a subtle 50 m reference grid, kept below the school fill
  const grid = new THREE.GridHelper(1600, 32, 0x9da195, 0xc7c2b5);
  grid.position.y = .026;
  grid.material.transparent = true;
  grid.material.opacity = .32;
  grid.material.depthWrite = false;
  G.grid.add(grid);

  /* ---------- geometry helpers ---------- */
  function cleanRing(points) {
    const p = points.map(q => [q[0], q[1]]);
    if (p.length > 1 && Math.hypot(p[0][0] - p[p.length - 1][0], p[0][1] - p[p.length - 1][1]) < .02) p.pop();
    return p;
  }

  function flatPolygon(points, y, material) {
    const pts = cleanRing(points);
    if (pts.length < 3) return null;
    const contour = pts.map(p => new THREE.Vector2(p[0], p[1]));
    let tris = [];
    try { tris = THREE.ShapeUtils.triangulateShape(contour, []); } catch (err) { return null; }
    if (!tris.length) return null;
    const pos = []; const idx = [];
    pts.forEach(p => pos.push(p[0], y, p[1]));
    tris.forEach(t => {
      const [a, b, c] = t;
      const cross = (pts[b][0] - pts[a][0]) * (pts[c][1] - pts[a][1]) - (pts[b][1] - pts[a][1]) * (pts[c][0] - pts[a][0]);
      if (cross > 0) idx.push(a, c, b); else idx.push(a, b, c);
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    const normals = [];
    for (let i = 0; i < pos.length; i += 3) normals.push(0, 1, 0);
    geo.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
    geo.setIndex(idx);
    const mesh = new THREE.Mesh(geo, material);
    mesh.receiveShadow = true;
    return mesh;
  }

  function flatRibbon(points, width, y, material) {
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

  function lineLoop(points, y, material) {
    const pts = cleanRing(points);
    const verts = pts.map(p => new THREE.Vector3(p[0], y, p[1]));
    const geo = new THREE.BufferGeometry().setFromPoints(verts);
    return new THREE.LineLoop(geo, material);
  }

  function linePath(points, y, material) {
    const verts = points.map(p => new THREE.Vector3(p[0], y, p[1]));
    const geo = new THREE.BufferGeometry().setFromPoints(verts);
    return new THREE.Line(geo, material);
  }

  function polylineMaterial(color, opacity = 1, dashed = false) {
    if (dashed) return new THREE.LineDashedMaterial({ color, transparent: opacity < 1, opacity, dashSize: 5, gapSize: 4 });
    return new THREE.LineBasicMaterial({ color, transparent: opacity < 1, opacity });
  }

  function dashedLine(points, y, color, opacity = 1) {
    const m = linePath(points, y, polylineMaterial(color, opacity, true));
    m.computeLineDistances();
    return m;
  }

  function flatLine(points, y, color, opacity = 1) {
    return linePath(points, y, polylineMaterial(color, opacity, false));
  }

  G.track = new THREE.Group();
  scene.add(G.track);

  /* ---------- school ground / boundary ---------- */
  const schoolGroundMat = new THREE.MeshStandardMaterial({
    color: COL.schoolGround, roughness: .97, metalness: 0, side: THREE.DoubleSide
  });
  const schoolGround = flatPolygon(DATA.school.polygon, .012, schoolGroundMat);
  if (schoolGround) {
    schoolGround.receiveShadow = true;
    G.ground.add(schoolGround);
  }
  const schoolLineMat = new THREE.LineBasicMaterial({ color: COL.schoolLine, transparent: true, opacity: .75 });
  G.ground.add(lineLoop(DATA.school.polygon, .036, schoolLineMat));
  const dashedBoundaryMat = new THREE.LineDashedMaterial({ color: 0x4e7058, transparent: true, opacity: .55, dashSize: 5, gapSize: 4 });
  const dashedBoundary = lineLoop(DATA.school.polygon, .046, dashedBoundaryMat);
  dashedBoundary.computeLineDistances();
  G.ground.add(dashedBoundary);
  const boundaryBand = flatRibbon(DATA.school.polygon, 2.0, .038, new THREE.MeshStandardMaterial({ color: 0x3f5142, roughness: .95, transparent: true, opacity: .62, side: THREE.DoubleSide }));
  if (boundaryBand) G.ground.add(boundaryBand);

  // other school boundaries are context only
  const otherLineMat = new THREE.LineDashedMaterial({ color: COL.context, transparent: true, opacity: .42, dashSize: 7, gapSize: 6 });
  for (const s of DATA.otherSchools || []) {
    const l = lineLoop(s.polygon, .03, otherLineMat);
    l.computeLineDistances();
    G.context.add(l);
  }

  /* ---------- landuse ---------- */
  for (const lu of DATA.landuse || []) {
    const isRes = lu.tags.landuse === 'residential';
    const m = new THREE.MeshStandardMaterial({
      color: isRes ? 0xdde0d4 : 0xd8ddcf,
      roughness: 1, transparent: true, opacity: .34, depthWrite: false, side: THREE.DoubleSide
    });
    const p = flatPolygon(lu.polygon, .004, m);
    if (p) G.landuse.add(p);
  }

  /* ---------- sports: track and pitches ---------- */
  const trackOuterMat = new THREE.MeshStandardMaterial({ color: COL.track, roughness: .96, metalness: 0, side: THREE.DoubleSide });
  const pitchMat = new THREE.MeshStandardMaterial({ color: COL.pitch, roughness: .98, metalness: 0, side: THREE.DoubleSide });
  if (DATA.track && DATA.track.outer) {
    const outer = flatPolygon(DATA.track.outer.polygon, .045, trackOuterMat);
    if (outer) G.track.add(outer);
    if (DATA.track.inner) {
      const inner = flatPolygon(DATA.track.inner.polygon, .058, pitchMat);
      if (inner) G.track.add(inner);
      // a fine white touchline is the only drawn line; no invented lane markings
      G.track.add(lineLoop(DATA.track.inner.polygon, .064, new THREE.LineBasicMaterial({ color: 0xf5f0e1, transparent: true, opacity: .55 })));
    }
  }
  for (const p of DATA.pitches || []) {
    if (DATA.track && DATA.track.inner && p.id === DATA.track.inner.id) continue;
    if (p.id === '638483883') continue;
    const m = flatPolygon(p.polygon, .052, pitchMat);
    if (m) G.sports.add(m);
    G.sports.add(lineLoop(p.polygon, .06, new THREE.LineBasicMaterial({ color: 0xf5f0e1, transparent: true, opacity: .4 })));
  }

  /* ---------- roads: OSM centerline only ---------- */
  const roadMat = new THREE.LineBasicMaterial({ color: COL.road, transparent: true, opacity: .82 });
  const footMat = new THREE.LineDashedMaterial({ color: 0x9a978c, transparent: true, opacity: .55, dashSize: 2.5, gapSize: 2.5 });
  for (const r of DATA.roads || []) {
    if (!r.points || r.points.length < 2) continue;
    const isFoot = r.highway === 'footway' || r.highway === 'path' || r.highway === 'steps';
    const line = linePath(r.points, .085, isFoot ? footMat : roadMat);
    if (isFoot) line.computeLineDistances();
    G.roads.add(line);
  }

  /* ---------- barriers ---------- */
  for (const b of DATA.barriers || []) {
    if (b.points && b.points.length > 1) {
      G.context.add(dashedLine(b.points, .075, 0x8e8a7d, .4));
    }
  }

  /* ---------- buildings ---------- */
  const buildingViews = [];
  const buildingPickMeshes = [];

  function makeBuilding(rec, inside) {
    const pts = cleanRing(rec.polygon);
    if (pts.length < 3) return;
    const group = new THREE.Group();
    const wallColor = inside ? COL.insideWall : COL.outsideWall;
    const topColor = inside ? COL.insideTop : COL.outsideTop;
    const wallMat = new THREE.MeshStandardMaterial({
      color: wallColor, roughness: .87, metalness: .02, side: THREE.DoubleSide,
      transparent: !inside, opacity: inside ? 1 : .56, depthWrite: inside
    });
    const topMat = new THREE.MeshStandardMaterial({
      color: topColor, roughness: .93, metalness: .01, side: THREE.DoubleSide,
      transparent: !inside, opacity: inside ? 1 : .48, depthWrite: inside
    });
    const edgeMat = new THREE.LineBasicMaterial({
      color: inside ? COL.edge : COL.edgeSoft,
      transparent: true, opacity: inside ? .78 : .30
    });

    // vertical walls (unit height 0..1; group.scale.y controls height)
    const pos = []; const idx = [];
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = pts[(i + 1) % pts.length];
      const base = pos.length / 3;
      pos.push(a[0], 0, a[1], b[0], 0, b[1], b[0], 1, b[1], a[0], 1, a[1]);
      idx.push(base, base + 1, base + 2, base, base + 2, base + 3);
    }
    const wallGeo = new THREE.BufferGeometry();
    wallGeo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    wallGeo.setIndex(idx);
    wallGeo.computeVertexNormals();
    const walls = new THREE.Mesh(wallGeo, wallMat);
    walls.castShadow = true;
    walls.receiveShadow = false;
    walls.userData.building = rec;
    group.add(walls);
    buildingPickMeshes.push(walls);

    // roof cap
    const contour = pts.map(p => new THREE.Vector2(p[0], p[1]));
    let tris = [];
    try { tris = THREE.ShapeUtils.triangulateShape(contour, []); } catch (err) { tris = []; }
    if (tris.length) {
      const rp = []; const ri = [];
      pts.forEach(p => rp.push(p[0], 1.002, p[1]));
      tris.forEach(t => {
        const [a, b, c] = t;
        const cross = (pts[b][0] - pts[a][0]) * (pts[c][1] - pts[a][1]) - (pts[b][1] - pts[a][1]) * (pts[c][0] - pts[a][0]);
        if (cross > 0) ri.push(a, c, b); else ri.push(a, b, c);
      });
      const roofGeo = new THREE.BufferGeometry();
      roofGeo.setAttribute('position', new THREE.Float32BufferAttribute(rp, 3));
      const ns = []; for (let i = 0; i < rp.length; i += 3) ns.push(0, 1, 0);
      roofGeo.setAttribute('normal', new THREE.Float32BufferAttribute(ns, 3));
      roofGeo.setIndex(ri);
      const roof = new THREE.Mesh(roofGeo, topMat);
      roof.castShadow = true;
      roof.receiveShadow = false;
      roof.userData.building = rec;
      group.add(roof);
      buildingPickMeshes.push(roof);
    }

    // edge segments: base, top and vertical corner lines
    const ep = [];
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = pts[(i + 1) % pts.length];
      ep.push(a[0], .004, a[1], b[0], .004, b[1]);
      ep.push(a[0], 1, a[1], b[0], 1, b[1]);
      ep.push(a[0], 0, a[1], a[0], 1, a[1]);
    }
    const eg = new THREE.BufferGeometry();
    eg.setAttribute('position', new THREE.Float32BufferAttribute(ep, 3));
    const edges = new THREE.LineSegments(eg, edgeMat);
    group.add(edges);

    group.scale.y = height;
    group.userData.rec = rec;
    (inside ? G.inside : G.outside).add(group);

    const view = { rec, inside, group, walls, roof: group.children[1] && group.children[1].type === 'Mesh' ? group.children[1] : null, wallMat, topMat, edgeMat, edges };
    rec._view = view;
    buildingViews.push(view);
  }

  for (const b of DATA.buildings) makeBuilding(b, b.inside);
  G.outside.visible = false;

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

  function makeYellowGridTexture() {
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
  LMAT.plaza = new THREE.MeshStandardMaterial({ color: 0xd2ae58, roughness: .96, metalness: 0 });
  LMAT.volley = new THREE.MeshStandardMaterial({ color: 0x6c8b8c, roughness: .95, metalness: 0 });
  function makeStoneTexture() {
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

  const CAMPUS_ROT = THREE.MathUtils.degToRad(10.3);
  const CAMPUS_BEARING = 169.7;
  const TRACK_SHIFT_X = -2;
  G.track.position.x = TRACK_SHIFT_X;
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
  const knownBuildingNames = { '638485974': '体育馆' };
  for (const b of DATA.buildings) {
    const listedName = b.name || knownBuildingNames[b.id];
    addFeature({
      kind: '建筑',
      name: listedName || ('OSM 建筑 ' + b.id),
      short: listedName || ('建筑 ' + b.id),
      x: b.centroid[0], z: b.centroid[1],
      y: height + 2.5,
      angle: polygonBearing(b.polygon),
      rec: b,
      layer: b.inside ? G.inside : G.outside
    });
  }
  for (const v of buildingViews) {
    const f = FEATURE_BY_REC.get(v.rec);
    if (f) f.group = v.group;
  }

  // the user's tennis block touches the gym: shift the gym (OSM way 638485974) east
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

  // 22–23: track and football field
  const innerC = DATA.track && DATA.track.inner ? DATA.track.inner.centroid : [0, 0];
  const outerC = DATA.track && DATA.track.outer ? DATA.track.outer.centroid : [0, 0];
  const trackFeat = addFeature({ kind: '场地', name: '田径场', x: outerC[0] + TRACK_SHIFT_X, z: outerC[1], y: 2.4, angle: CAMPUS_BEARING, layer: G.sports });
  trackFeat.group = G.track;
  addFeature({ kind: '场地', name: '足球场', x: innerC[0] + TRACK_SHIFT_X, z: innerC[1] - 21, y: 2.4, angle: CAMPUS_BEARING, layer: G.sports });

  // 24: four basketball courts + three volleyball courts on the top row
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
    const feat = addFeature({ kind: '球场', name: '篮球场 ×4 / 排球场 ×3', x: bcx, z: bcz, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });
    feat.group = g;
  } else {
    addFeature({ kind: '球场', name: '篮球场 ×4 / 排球场 ×3', x: -46, z: -47.5, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });
  }

  // 25–26: two tennis courts from the user's (-171.40,53.74) — (-140.82,119.51) block
  const tennisDefs = [
    { name: '网球场 A', x: -156.11, z: 70.18 },
    { name: '网球场 B', x: -156.11, z: 103.07 }
  ];
  for (const tf of tennisDefs) {
    const cw = 24, cd = 32.885;
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
    const feat = addFeature({ kind: '球场', name: tf.name, x: tf.x, z: tf.z, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });
    feat.group = g;
  }

  // 27: covered grandstand south of the track
  (() => {
    const gx = -115.04, gz = 60.68;
    const g = new THREE.Group(); g.position.set(gx, 0, gz); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);
    for (let i = 0; i < 6; i++) {
      const h = .42 * (i + 1);
      lmBox(18, h, 1.25, i % 2 ? LMAT.seat : LMAT.concrete, 0, h / 2, -3.6 + i * 1.25, g);
    }
    for (const x of [-8.2, 8.2]) for (const z of [-3.7, 3.7]) lmCyl(.17, .2, 5.7, 8, LMAT.metal, x, 2.85, z, g);
    lmBox(19.5, .3, 8.2, LMAT.white, 0, 5.85, 0, g);
    lmBox(18.5, .18, 1.0, LMAT.concreteDark, 0, .1, -4.25, g);
    const feat = addFeature({ kind: '看台', name: '主席台（南看台）', x: gx, z: gz, y: 7, angle: 79.7, layer: G.landmarks });
    feat.group = g;
  })();

  // 28: platform + membrane canopy on the east edge of the track
  (() => {
    const px = -79.06, pz = -38.45;
    const g = new THREE.Group(); g.position.set(px, 0, pz); g.rotation.y = CAMPUS_ROT; G.landmarks.add(g);
    lmBox(8, 1.15, 36.05, LMAT.concrete, 0, .58, 0, g);
    for (const x of [-3.2, 3.2]) for (const z of [-17, 0, 17]) lmCyl(.17, .2, 6.0, 8, LMAT.metal, x, 3.0, z, g);
    const roof = new THREE.Mesh(new THREE.SphereGeometry(1, 30, 14, 0, Math.PI * 2, 0, Math.PI / 2), LMAT.white);
    roof.scale.set(5.2, 1.4, 18.5); roof.position.set(0, 6.1, 0); g.add(lmAdd(roof));
    lmBox(12, .25, 36.5, LMAT.white, 0, 6.05, 0, g);
    const feat = addFeature({ kind: '平台', name: '台下平台 · 膜结构', x: px, z: pz, y: 8, angle: CAMPUS_BEARING, layer: G.landmarks });
    feat.group = g;
  })();

  // 29: the real stone main gate, on the user-supplied line (154,-95) -> (118,-125)
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
    const feat = addFeature({ kind: '大门', name: '大门', x: gateX, z: gateZ, y: 12, angle: Math.round(gateBearing * 10) / 10, layer: G.landmarks });
    feat.group = g;
  })();

  // user's gate reference line, kept in the guide layer
  {
    const gm = new THREE.LineDashedMaterial({ color: 0xb45b3e, transparent: true, opacity: .55, dashSize: 3, gapSize: 2 });
    const gl = new THREE.Line(new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(gateA[0], .32, gateA[1]), new THREE.Vector3(gateB[0], .32, gateB[1])
    ]), gm);
    gl.computeLineDistances(); G.guide.add(gl);
  }

  // 32: the yellow-grid circular plaza in the entrance area
  let plazaGroup = null;
  const plazaX = 99.13, plazaZ = -80.445, plazaRX = 57.6418, plazaRZ = 18.5498;
  const PLAZA_ROT = THREE.MathUtils.degToRad(50.9746);
  (() => {
    const g = new THREE.Group(); g.position.set(plazaX, 0, plazaZ); g.rotation.y = PLAZA_ROT; G.landmarks.add(g); plazaGroup = g;
    const disc = new THREE.Mesh(new THREE.CircleGeometry(1, 96), LMAT.plaza);
    disc.rotation.x = -Math.PI / 2; disc.scale.set(plazaRX, plazaRZ, 1); disc.position.y = .036;
    g.add(lmAdd(disc, false, true));
    const ring = new THREE.Mesh(new THREE.RingGeometry(.97, 1, 96), LMAT.concreteDark);
    ring.rotation.x = -Math.PI / 2; ring.scale.set(plazaRX, plazaRZ, 1); ring.position.y = .042;
    g.add(lmAdd(ring, false, true));
    // grid inside the ellipse; drawn as line segments so it is clipped to the ellipse
    const gp = [];
    for (let lx = -plazaRX + 4; lx < plazaRX; lx += 4) {
      const hz = plazaRZ * Math.sqrt(Math.max(0, 1 - (lx / plazaRX) ** 2));
      gp.push(lx, .046, -hz, lx, .046, hz);
    }
    for (let lz = -plazaRZ + 4; lz < plazaRZ; lz += 4) {
      const hx = plazaRX * Math.sqrt(Math.max(0, 1 - (lz / plazaRZ) ** 2));
      gp.push(-hx, .046, lz, hx, .046, lz);
    }
    const gg = new THREE.BufferGeometry();
    gg.setAttribute('position', new THREE.Float32BufferAttribute(gp, 3));
    g.add(new THREE.LineSegments(gg, new THREE.LineBasicMaterial({ color: 0x7b5a24, transparent: true, opacity: .8 })));
  })();

  // 30: fountain inside the southeast gate
  (() => {
    const fx = 105.93, fz = -70.41;
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
    const feat = addFeature({ kind: '喷泉', name: '喷泉', x: fx, z: fz, y: 4, angle: 0, layer: G.landmarks });
    feat.group = g;
  })();

  // 31: school boundary (annotation, no extra geometry)
  addFeature({ kind: '边界', name: '校园边界', x: 0, z: -153, y: 2, angle: 0, layer: G.ground });
  const plazaFeat = addFeature({ kind: '广场', name: '黄色网格椭圆广场', x: 99.13, z: -80.445, y: 2, angle: 50.97, layer: G.landmarks });
  plazaFeat.group = plazaGroup;

  // 33: editable boundary wall
  const wallGroup = new THREE.Group();
  G.context.add(wallGroup);
  {
    const poly = DATA.school.polygon;
    for (let i = 0; i < poly.length; i++) {
      const a = poly[i], b = poly[(i + 1) % poly.length];
      const dx = b[0] - a[0], dz = b[1] - a[1];
      const len = Math.hypot(dx, dz);
      if (len < .2) continue;
      const mx = (a[0] + b[0]) / 2, mz = (a[1] + b[1]) / 2;
      const ry = Math.atan2(-dz, dx);
      lmBox(len, 2.3, .45, LMAT.concrete, mx, 1.15, mz, wallGroup, ry);
    }
    const wf = addFeature({ kind: '围墙', name: '校园围墙', x: 0, z: -153, y: 4, angle: 0, layer: G.context });
    wf.group = wallGroup;
  }



  /* ---------- free-fly camera ---------- */
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
    if (name === 'walk') { if (WALK.active) leaveWalk(true); else enterWalk(); return; }
    if (WALK.active) leaveWalk(false);
    if (name === 'upright') {
      setCameraTo(new THREE.Vector3(0, 0, 0), 0, .055, phoneLayout() ? 910 : 610);
      fly.yaw += 10.3 * Math.PI / 180;
      camera.rotation.set(fly.pitch, fly.yaw, 0, 'YXZ');
      view.auto = false;
      const a = $('#autoBtn'); if (a) a.classList.remove('active');
      $$('.view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === 'upright'));
      return;
    }
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

  function aimAtPoint(x, y, z) {
    const dir = new THREE.Vector3(x, y, z).sub(camera.position);
    if (dir.lengthSq() < .001) return;
    dir.normalize();
    fly.pitch = Math.asin(clamp(dir.y, -1, 1));
    fly.yaw = Math.atan2(-dir.x, -dir.z);
    camera.rotation.set(fly.pitch, fly.yaw, 0, 'YXZ');
  }
  function focusFeature(f) {
    if (WALK.active) leaveWalk(false);
    const wide = f.kind === '场地' || f.kind === '球场' || f.kind === '边界';
    const off = wide ? 220 : (f.kind === '建筑' ? 100 : 95);
    const targetY = f.kind === '建筑' ? Math.min(height * .5, 7) : 2.2;
    camera.position.set(f.x + off * .75, Math.max(55, off * .6), f.z + off * .75);
    aimAtPoint(f.x, targetY, f.z);
    view.userMoved = true;
    view.auto = false;
    const auto = $('#autoBtn'); if (auto) auto.classList.remove('active');
  }

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


  /* ---------- pointer / orbit ---------- */
  const el = renderer.domElement;
  let drag = null;
  let hoverRec = null;
  let selectedRec = null;
  let moved = 0;
  const pointers = new Map();
  let pinchStart = 0, pinchRadius = 0;

  function screenToNdc(clientX, clientY) {
    const r = el.getBoundingClientRect();
    return { x: ((clientX - r.left) / r.width) * 2 - 1, y: -((clientY - r.top) / r.height) * 2 + 1 };
  }

  function pickAt(clientX, clientY) {
    const nd = screenToNdc(clientX, clientY);
    const ray = new THREE.Raycaster();
    ray.setFromCamera(new THREE.Vector2(nd.x, nd.y), camera);
    const active = buildingPickMeshes.filter(m => {
      let p = m;
      while (p) { if (p.visible === false) return false; p = p.parent; }
      return true;
    });
    const hit = ray.intersectObjects(active, false)[0];
    return hit ? hit.object.userData.building : null;
  }

  function setHighlight(rec, mode) {
    if (!rec || !rec._view) return;
    const v = rec._view;
    const active = mode === 'selected' ? COL.accent : (mode === 'hover' ? COL.hover : 0x000000);
    const intensity = mode === 'selected' ? .27 : (mode === 'hover' ? .16 : 0);
    v.wallMat.emissive.setHex(active);
    v.wallMat.emissiveIntensity = intensity;
    v.topMat.emissive.setHex(active);
    v.topMat.emissiveIntensity = intensity;
    v.edgeMat.color.setHex(mode === 'selected' ? COL.accent : (mode === 'hover' ? COL.hover : (v.inside ? COL.edge : COL.edgeSoft)));
    v.edgeMat.opacity = mode ? .92 : (v.inside ? .54 : .26);
  }

  function refreshHighlight() {
    for (const v of buildingViews) setHighlight(v.rec, v.rec === selectedRec ? 'selected' : (v.rec === hoverRec ? 'hover' : 'none'));
  }

  function showBuilding(rec) {
    const block = $('#selectedInfo');
    const empty = $('#selectedEmpty');
    if (!rec) {
      selectedRec = null;
      block.hidden = true;
      empty.hidden = false;
      $('#clearSelection').hidden = true;
      if (dbgSel) dbgSel.textContent = '—';
      refreshHighlight();
      return;
    }
    selectedRec = rec;
    empty.hidden = true;
    block.hidden = false;
    $('#clearSelection').hidden = false;
    const f = FEATURE_BY_REC.get(rec);
    $('#selTitle').textContent = f ? ('#' + f.label + ' · ' + (rec.name || 'OSM 建筑')) : (rec.name || ('OSM 建筑 · ' + rec.id));
    const lc = f ? worldToLocal(f.x, f.z) : null;
    $('#selSub').textContent = 'way ' + rec.id + ' · ' + (rec.inside ? '校界内' : '校界外') + (f ? (' · X ' + fmtCoord(lc.x) + ' · Z ' + fmtCoord(lc.z) + ' · θ ' + f.angle.toFixed(1) + '°') : '');
    if (dbgSel && f) dbgSel.textContent = '#' + f.label + ' ' + (rec.name || '建筑') + ' · ' + featureCoord(f);
    $('#selArea').textContent = fmt(rec.area, 0) + ' m²';
    $('#selVerts').textContent = rec.vertices + ' 点';
    $('#selHeight').textContent = height + ' m（示意）';
    const tags = $('#selTags');
    tags.innerHTML = '';
    for (const [k, v] of Object.entries(rec.tags || {})) {
      const span = document.createElement('span');
      span.className = 'tag';
      span.textContent = k + '=' + v;
      tags.appendChild(span);
    }
  }

  function setHover(rec) {
    if (rec === hoverRec) return;
    hoverRec = rec;
    refreshHighlight();
  }

  el.addEventListener('contextmenu', e => e.preventDefault());

  el.addEventListener('pointerdown', e => {
    if (e.pointerType === 'touch') { touchPointerDown(e); return; }
    if (e.button !== 0) return;
    drag = {
      mode: 'look',
      x: e.clientX, y: e.clientY, lastX: e.clientX, lastY: e.clientY,
      moved: 0
    };
    moved = 0;
    el.setPointerCapture(e.pointerId);
    view.userMoved = true;
    if (view.auto) { view.auto = false; $('#autoBtn').classList.remove('active'); }
  });

  el.addEventListener('pointermove', e => {
    setGroundFromPointer(e.clientX, e.clientY);
    if (e.pointerType === 'touch') { touchPointerMove(e); return; }
    if (drag) {
      const dx = e.clientX - drag.lastX;
      const dy = e.clientY - drag.lastY;
      drag.lastX = e.clientX; drag.lastY = e.clientY;
      drag.moved += Math.abs(dx) + Math.abs(dy);
      moved = drag.moved;
      fly.yaw -= dx * .0038;
      fly.pitch = clamp(fly.pitch - dy * .0038, -1.45, 1.45);
      return;
    }
    const rec = pickAt(e.clientX, e.clientY);
    setHover(rec);
    if (rec) {
      tooltipEl.textContent = 'way ' + rec.id + ' · ' + fmt(rec.area, 0) + ' m² · ' + (rec.inside ? '校界内' : '校界外');
      tooltipEl.style.left = e.clientX + 'px';
      tooltipEl.style.top = e.clientY + 'px';
      tooltipEl.classList.add('show');
      el.style.cursor = 'pointer';
    } else {
      tooltipEl.classList.remove('show');
      el.style.cursor = 'default';
    }
  });

  el.addEventListener('pointerleave', () => { if (dbgGround) dbgGround.textContent = 'X —  Z —'; });
  el.addEventListener('pointerup', e => {
    if (e.pointerType === 'touch') { touchPointerUp(e); return; }
    if (drag) {
      if (drag.moved < 6) {
        if (editorMode) {
          const t = pickEditTarget(e.clientX, e.clientY);
          if (t) selectEditTarget(t);
        } else {
          const rec = pickAt(e.clientX, e.clientY);
          showBuilding(rec);
        }
      }
      drag = null;
    }
  });
  el.addEventListener('pointercancel', () => { drag = null; pointers.clear(); });

  el.addEventListener('wheel', e => {
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

  /* ---------- feature labels / numbers ---------- */
  const labelDefs = [];
  let labelsOn = true;
  let codesOn = true;
  function addLabel(text, x, y, z, kind = '', layer = null, code = false) {
    const div = document.createElement('div');
    div.className = 'map-label ' + kind;
    div.textContent = text;
    labelsEl.appendChild(div);
    const def = { el: div, x, y, z, kind, layer, code };
    labelDefs.push(def);
    return def;
  }

  const schoolRec = DATA.school;
  addLabel(schoolRec.name || '学校', 0, 28, 0, 'school');
  for (const s of DATA.otherSchools || []) {
    if (s.name) addLabel(s.name, s.centroid[0], 18, s.centroid[1], 'context', G.context);
  }
  const roadNames = new Map();
  for (const r of DATA.roads) {
    if (!r.name) continue;
    const prev = roadNames.get(r.name);
    if (!prev || r.points.length > prev.points.length) roadNames.set(r.name, r);
  }
  for (const [name, r] of roadNames) {
    const mid = r.points[Math.floor(r.points.length / 2)];
    if (Math.abs(mid[0]) < 520 && Math.abs(mid[1]) < 360) addLabel(name, mid[0], 1.2, mid[1], 'road', G.roads);
  }

  // 01–31: numbers on buildings and real-scene landmarks
  for (const f of FEATURES) {
    if (f.kind === '建筑') {
      f.labelDef = addLabel('#' + f.label, f.x, f.y, f.z, 'code' + (f.rec && !f.rec.inside ? ' outside' : ''), f.layer, true);
    } else {
      f.labelDef = addLabel('#' + f.label + ' ' + f.name, f.x, f.y, f.z, 'feature', f.layer, false);
    }
  }

  const labelVec = new THREE.Vector3();
  const camDir = new THREE.Vector3();
  function updateLabels() {
    camera.getWorldDirection(camDir);
    const w = window.innerWidth, h = window.innerHeight;
    for (const l of labelDefs) {
      const visible = (l.code ? codesOn : labelsOn) && (!l.layer || l.layer.visible);
      if (!visible) { l.el.classList.remove('show'); continue; }
      labelVec.set(l.x, l.y, l.z);
      const to = labelVec.clone().sub(camera.position);
      if (to.dot(camDir) <= 0) { l.el.classList.remove('show'); continue; }
      labelVec.project(camera);
      if (labelVec.z > 1 || labelVec.z < -1) { l.el.classList.remove('show'); continue; }
      const sx = (labelVec.x * .5 + .5) * w;
      const sy = (-labelVec.y * .5 + .5) * h;
      if (sx < -100 || sx > w + 100 || sy < -40 || sy > h + 40) { l.el.classList.remove('show'); continue; }
      l.el.style.left = sx + 'px';
      l.el.style.top = sy + 'px';
      l.el.classList.add('show');
    }
  }

  function fmtCoord(v) { return (v >= 0 ? '+' : '') + v.toFixed(1); }
  function featureCoord(f) { const lc = worldToLocal(f.x, f.z); return 'X ' + fmtCoord(lc.x) + ' · Z ' + fmtCoord(lc.z) + ' · θ ' + f.angle.toFixed(1) + '°'; }

  /* ---------- campus-local coordinates (screen-straight in 摆正 view) ---------- */
  const LOCAL_ROT = CAMPUS_ROT;
  const LOCAL_C = Math.cos(LOCAL_ROT), LOCAL_S = Math.sin(LOCAL_ROT);
  function worldToLocal(x, z) { return { x: x * LOCAL_C - z * LOCAL_S, z: x * LOCAL_S + z * LOCAL_C }; }
  function localToWorld(x, z) { return { x: x * LOCAL_C + z * LOCAL_S, z: -x * LOCAL_S + z * LOCAL_C }; }

  /* ---------- index list ---------- */
  function updateIndex() {
    const list = $('#indexList');
    if (!list) return;
    list.textContent = '';
    for (const f of FEATURES) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'idx-row';
      const no = document.createElement('b'); no.textContent = '#' + f.label;
      const nm = document.createElement('span');
      nm.textContent = (f.rec && f.rec.name ? f.rec.name : f.name) + (f.rec && !f.rec.inside ? ' · 校外' : '');
      const em = document.createElement('em'); em.textContent = 'θ ' + f.angle.toFixed(1) + '°';
      const lc = worldToLocal(f.x, f.z);
      const co = document.createElement('i'); co.textContent = 'X ' + fmtCoord(lc.x) + ' · Z ' + fmtCoord(lc.z);
      btn.append(no, nm, em, co);
      btn.title = '定位到 #' + f.label;
      btn.addEventListener('click', () => {
        $$('.idx-row').forEach(x => x.classList.remove('active'));
        btn.classList.add('active');
        if (editorMode && f.edit) { selectEditTarget(f.edit); return; }
        focusFeature(f);
        if (f.rec) showBuilding(f.rec);
        else $('#dbgSel').textContent = '#' + f.label + ' ' + f.name + ' · ' + featureCoord(f);
      });
      list.appendChild(btn);
    }
    $('#indexCount').textContent = FEATURES.length;
  }
  updateIndex();

  /* ---------- debug HUD ---------- */
  const dbgCam = $('#dbgCam'), dbgAng = $('#dbgAng'), dbgGround = $('#dbgGround'), dbgSel = $('#dbgSel');
  const groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  const groundRay = new THREE.Raycaster();
  const groundNdc = new THREE.Vector2();
  const groundHit = new THREE.Vector3();
  function setGroundFromPointer(clientX, clientY) {
    if (!dbgGround) return;
    const nd = screenToNdc(clientX, clientY);
    groundNdc.set(nd.x, nd.y);
    groundRay.setFromCamera(groundNdc, camera);
    if (groundRay.ray.intersectPlane(groundPlane, groundHit)) {
      const lc = worldToLocal(groundHit.x, groundHit.z);
      dbgGround.textContent = 'X ' + fmtCoord(lc.x) + '  Z ' + fmtCoord(lc.z);
    } else {
      dbgGround.textContent = 'X —  Z —';
    }
  }
  function updateDebugHud() {
    if (!dbgCam) return;
    const lc = worldToLocal(camera.position.x, camera.position.z);
    dbgCam.textContent = 'X ' + fmtCoord(lc.x) + '  Y ' + camera.position.y.toFixed(1) + '  Z ' + fmtCoord(lc.z);
    const heading = (((-fly.yaw * 180 / Math.PI) % 360) + 360) % 360;
    dbgAng.textContent = 'HDG ' + heading.toFixed(1) + '° / PITCH ' + (fly.pitch * 180 / Math.PI).toFixed(1) + '°';
  }

  /* ================= object editor ================= */
  let editorMode = false;
  const EDIT = {
    targets: [], selected: null, history: [], hi: -1,
    pickMeshes: [], box: null
  };
  const EDIT_LS = 'xmfls-layout-v1';

  function editLabelName(f) {
    return '#' + f.label + ' · ' + (f.name || '对象');
  }

  for (const f of FEATURES) {
    if (!f.group) continue;
    const g = f.group;
    const isBuilding = f.kind === '建筑';
    const isEllipse = f.kind === '广场' || f.label === '32';
    const geomX = f.x - g.position.x;
    const geomZ = f.z - g.position.z;
    const lc0 = worldToLocal(f.x, f.z);
    const baseLabelY = f.labelDef ? f.labelDef.y : f.y;
    const state = {
      x: lc0.x, z: lc0.z, y: g.position.y,
      rot: g.rotation.y, h: g.scale.y
    };
    if (isEllipse) { state.rx = 57.6418 * 2; state.rz = 18.5498 * 2; }
    const t = {
      id: f.label, no: f.no, name: f.name, kind: f.kind,
      isBuilding, isEllipse, f, group: g, geomX, geomZ, baseLabelY,
      initial: { ...state }, state
    };
    f.edit = t;
    EDIT.targets.push(t);
    g.traverse(o => {
      if (o.isMesh) {
        o.userData.editTarget = t;
        EDIT.pickMeshes.push(o);
      }
    });
  }
  EDIT.targets.sort((a, b) => Number(a.no) - Number(b.no));

  const editBox = new THREE.BoxHelper(new THREE.Object3D(), 0xa75437);
  editBox.visible = false;
  scene.add(editBox);
  EDIT.box = editBox;

  const editRay = new THREE.Raycaster();
  const editNdc = new THREE.Vector2();

  function pickEditTarget(clientX, clientY) {
    const nd = screenToNdc(clientX, clientY);
    editNdc.set(nd.x, nd.y);
    editRay.setFromCamera(editNdc, camera);
    const hits = editRay.intersectObjects(EDIT.pickMeshes, false);
    for (const h of hits) {
      if (h.object && h.object.userData.editTarget) return h.object.userData.editTarget;
    }
    return null;
  }

  function snapshotState() {
    return EDIT.targets.map(t => ({
      id: t.id,
      x: +t.state.x.toFixed(3), z: +t.state.z.toFixed(3),
      y: +t.state.y.toFixed(3), rot: +t.state.rot.toFixed(5),
      h: +t.state.h.toFixed(3),
      rx: t.isEllipse ? +t.state.rx.toFixed(3) : undefined,
      rz: t.isEllipse ? +t.state.rz.toFixed(3) : undefined
    }));
  }

  function applyTarget(t) {
    const s = t.state;
    const w = localToWorld(s.x, s.z);
    t.group.position.x = w.x - t.geomX;
    t.group.position.z = w.z - t.geomZ;
    t.group.position.y = s.y;
    t.group.rotation.y = s.rot;
    t.group.scale.y = s.h;
    if (t.isEllipse) {
      t.group.scale.x = (s.rx / 2) / 57.6418;
      t.group.scale.z = (s.rz / 2) / 18.5498;
    }
    t.f.x = w.x; t.f.z = w.z;
    if (t.f.labelDef) {
      t.f.labelDef.x = w.x;
      t.f.labelDef.z = w.z;
      if (t.isBuilding) {
        t.f.y = s.y + s.h + 2.5;
        t.f.labelDef.y = t.f.y;
      } else {
        t.f.y = t.baseLabelY + (s.y - t.initial.y);
        t.f.labelDef.y = t.f.y;
      }
    }
    if (Math.abs(s.rot - t.initial.rot) > 1e-6) {
      t.f.angle = ((s.rot * 180 / Math.PI) % 180 + 180) % 180;
    }
    if (EDIT.selected === t) {
      editBox.setFromObject(t.group);
      fillEditFields();
      if (t.isBuilding) {
        $('#selHeight').textContent = s.h.toFixed(1) + ' m（已编辑）';
      }
    }
  }

  function applySnapshot(snap) {
    const byId = new Map(snap.map(s => [s.id, s]));
    for (const t of EDIT.targets) {
      const s = byId.get(t.id);
      if (!s) continue;
      t.state = { ...t.state, ...s };
      applyTarget(t);
    }
    if (EDIT.selected) editBox.setFromObject(EDIT.selected.group);
  }

  function updateHistoryButtons() {
    const u = $('#undoEdit'), r = $('#redoEdit');
    if (u) u.disabled = EDIT.hi <= 0;
    if (r) r.disabled = EDIT.hi >= EDIT.history.length - 1;
  }

  function saveLocal() {
    try {
      localStorage.setItem(EDIT_LS, JSON.stringify({
        format: 'xmfls-layout', version: 1, savedAt: new Date().toISOString(),
        objects: snapshotState()
      }));
    } catch (e) {}
  }

  function commitHistory() {
    const s = snapshotState();
    const cur = EDIT.history[EDIT.hi];
    if (cur && JSON.stringify(cur) === JSON.stringify(s)) {
      updateHistoryButtons(); return;
    }
    EDIT.history = EDIT.history.slice(0, EDIT.hi + 1);
    EDIT.history.push(s);
    EDIT.hi = EDIT.history.length - 1;
    saveLocal();
    updateHistoryButtons();
    if (typeof updateIndex === 'function') updateIndex();
    setEditStatus('已记录修改');
  }

  function undoEdit() {
    if (EDIT.hi <= 0) return;
    EDIT.hi--;
    applySnapshot(EDIT.history[EDIT.hi]);
    saveLocal();
    updateHistoryButtons();
    setEditStatus('已撤销');
  }
  function redoEdit() {
    if (EDIT.hi >= EDIT.history.length - 1) return;
    EDIT.hi++;
    applySnapshot(EDIT.history[EDIT.hi]);
    saveLocal();
    updateHistoryButtons();
    setEditStatus('已反撤销');
  }

  function fillEditFields() {
    const t = EDIT.selected;
    if (!t) return;
    $('#edX').value = t.state.x.toFixed(2);
    $('#edZ').value = t.state.z.toFixed(2);
    $('#edY').value = t.state.y.toFixed(2);
    $('#edR').value = (((t.state.rot * 180 / Math.PI) % 360 + 360) % 360).toFixed(1);
    $('#edH').value = t.isBuilding ? t.state.h.toFixed(2) : t.state.h.toFixed(3);
    $('#edHLabel').textContent = t.isBuilding ? '高度' : '高度×';
    $('#edHUnit').textContent = t.isBuilding ? 'm' : '×';
    const ef = $('#ellipseFields');
    if (ef) ef.hidden = !t.isEllipse;
    if (t.isEllipse && $('#edA')) {
      $('#edA').value = t.state.rx.toFixed(1);
      $('#edB').value = t.state.rz.toFixed(1);
    }
    $('#editHeightNote').textContent = t.isBuilding ? '该建筑单独高度（米）；不影响其他建筑。' : '补全构筑物的垂直缩放；椭圆可用 Y 位置整体抬升。';
  }

  function selectEditTarget(t) {
    EDIT.selected = t || null;
    const form = $('#editForm'), empty = $('#editEmpty');
    if (!t) {
      form.hidden = true; empty.hidden = false;
      editBox.visible = false;
      $('#editModeLabel').textContent = '选择对象';
      $('#editName').textContent = '—';
      $('#editStatus').textContent = '';
      return;
    }
    empty.hidden = true; form.hidden = false;
    $('#editModeLabel').textContent = '已选 #' + t.id;
    $('#editName').textContent = editLabelName(t.f);
    fillEditFields();
    editBox.setFromObject(t.group);
    editBox.visible = true;
    if (t.isBuilding && t.f.rec) {
      showBuilding(t.f.rec);
      $('#selHeight').textContent = t.state.h.toFixed(1) + ' m（已编辑）';
    } else {
      dbgSel.textContent = editLabelName(t.f) + ' · X ' + fmtCoord(t.state.x) + ' · Z ' + fmtCoord(t.state.z);
    }
    const panel = $('#panel');
    if (panel && panel.scrollTop > 0) {
      const block = $('#editBlock');
      if (block) block.scrollIntoView({ block: 'nearest' });
    }
  }

  function setEditStatus(msg) {
    const el = $('#editStatus');
    if (el) el.textContent = msg || '';
  }

  function setEditorMode(on) {
    editorMode = !!on;
    const block = $('#editBlock'), btn = $('#editToggle');
    if (block) block.hidden = !editorMode;
    if (btn) {
      btn.classList.toggle('active', editorMode);
      btn.textContent = editorMode ? '退出编辑' : '编辑';
    }
    const slider = $('#heightSlider');
    if (slider) slider.disabled = editorMode;
    if (!editorMode) {
      editBox.visible = false;
      setEditStatus('已退出编辑模式');
    } else {
      if (!WALK.active) setView('upright');
      selectEditTarget(EDIT.selected || null);
      setEditStatus('编辑模式：点击对象选择；高度滑块已停用');
    }
  }

  function setEditField(key, value, commit) {
    const t = EDIT.selected;
    if (!t || !Number.isFinite(value)) return;
    if (key === 'x' || key === 'z') t.state[key] = value;
    if (key === 'y') t.state.y = value;
    if (key === 'rot') t.state.rot = value * Math.PI / 180;
    if (key === 'h') {
      t.state.h = t.isBuilding ? Math.max(1, Math.min(80, value)) : Math.max(.05, Math.min(20, value));
    }
    if (key === 'a' || key === 'b') {
      if (!t.isEllipse) return;
      const v = Math.max(4, Math.min(400, value));
      if (key === 'a') t.state.rx = v; else t.state.rz = v;
    }
    applyTarget(t);
    if (commit) commitHistory();
  }

  function nudgeEdit(field, dir) {
    const t = EDIT.selected;
    if (!t) return;
    const step = field === 'x' || field === 'z' || field === 'y' ? .5 : (field === 'rot' ? 1 : (field === 'a' || field === 'b' ? 1 : (t.isBuilding ? .5 : .05)));
    let v;
    if (field === 'rot') v = (((t.state.rot * 180 / Math.PI) % 360 + 360) % 360) + step * dir;
    else if (field === 'a' || field === 'b') v = t.state[field === 'a' ? 'rx' : 'rz'] + step * dir;
    else v = t.state[field] + step * dir;
    setEditField(field, v, true);
    fillEditFields();
  }

  function exportEdits() {
    const payload = {
      format: 'xmfls-layout', version: 1,
      exportedAt: new Date().toISOString(),
      objects: snapshotState()
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'xmfls-layout-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    setEditStatus('已导出 ' + payload.objects.length + ' 个对象');
  }

  function importEdits(text) {
    let data;
    try { data = JSON.parse(text); } catch (e) { setEditStatus('JSON 解析失败'); return; }
    const list = Array.isArray(data) ? data : data.objects;
    if (!Array.isArray(list)) { setEditStatus('找不到 objects 数组'); return; }
    const byId = new Map(EDIT.targets.map(t => [t.id, t]));
    let n = 0;
    for (const o of list) {
      const t = byId.get(String(o.id));
      if (!t) continue;
      if (Number.isFinite(o.x)) t.state.x = o.x;
      if (Number.isFinite(o.z)) t.state.z = o.z;
      if (Number.isFinite(o.y)) t.state.y = o.y;
      if (Number.isFinite(o.rot)) t.state.rot = o.rot;
      if (Number.isFinite(o.h)) t.state.h = o.h;
      if (t.isEllipse && Number.isFinite(o.rx)) t.state.rx = o.rx;
      if (t.isEllipse && Number.isFinite(o.rz)) t.state.rz = o.rz;
      applyTarget(t); n++;
    }
    commitHistory();
    if (EDIT.selected) selectEditTarget(EDIT.selected);
    setEditStatus('已导入 ' + n + ' 个对象');
  }

  // restore local layout if valid
  const initialSnapshot = snapshotState();
  let restored = false;
  try {
    const raw = localStorage.getItem(EDIT_LS);
    if (raw) {
      const data = JSON.parse(raw);
      if (data && Array.isArray(data.objects) && data.objects.length) {
        applySnapshot(data.objects);
        restored = true;
      }
    }
  } catch (e) {}
  EDIT.initialSnapshot = initialSnapshot;
  EDIT.history = [initialSnapshot, snapshotState()];
  EDIT.hi = 1;
  if (!restored) { EDIT.history = [initialSnapshot]; EDIT.hi = 0; }
  updateHistoryButtons();
  if (restored) setEditStatus('已恢复上次编辑；可撤销回到原始');

  // wire editor UI
  $('#editToggle').addEventListener('click', () => setEditorMode(!editorMode));
  $('#closeEdit').addEventListener('click', () => setEditorMode(false));
  $('#undoEdit').addEventListener('click', undoEdit);
  $('#redoEdit').addEventListener('click', redoEdit);
  $('#exportEdit').addEventListener('click', exportEdits);
  $('#importEdit').addEventListener('click', () => $('#importFile').click());
  $('#importFile').addEventListener('change', e => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => importEdits(reader.result);
    reader.readAsText(f);
    e.target.value = '';
  });
  $('#resetObj').addEventListener('click', () => {
    if (!EDIT.selected) return;
    EDIT.selected.state = { ...EDIT.selected.initial };
    applyTarget(EDIT.selected);
    commitHistory(); fillEditFields();
  });
  $('#resetAll').addEventListener('click', () => {
    for (const t of EDIT.targets) { t.state = { ...t.initial }; applyTarget(t); }
    commitHistory();
    if (EDIT.selected) selectEditTarget(EDIT.selected);
  });
  $$('.nudge').forEach(btn => btn.addEventListener('click', () => nudgeEdit(btn.dataset.field, Number(btn.dataset.dir))));
  const fieldMap = { edX: 'x', edZ: 'z', edY: 'y', edR: 'rot', edH: 'h', edA: 'a', edB: 'b' };
  for (const [id, key] of Object.entries(fieldMap)) {
    const input = $('#' + id);
    input.addEventListener('input', () => setEditField(key, parseFloat(input.value), false));
    input.addEventListener('change', () => setEditField(key, parseFloat(input.value), true));
  }
  window.addEventListener('keydown', e => {
    if (!editorMode) return;
    if (e.ctrlKey || e.metaKey) {
      if (e.code === 'KeyZ') { e.preventDefault(); if (e.shiftKey) redoEdit(); else undoEdit(); }
      if (e.code === 'KeyY') { e.preventDefault(); redoEdit(); }
    }
  });

  // integrated real-image overlay modal
  $('#overlayBtn').addEventListener('click', () => {
    const modal = $('#overlayModal'), frame = $('#overlayFrame');
    if (frame && !frame.getAttribute('src')) {
      frame.setAttribute('src', window.__CALIB_PAGE || '../dist/坐标校准-实景叠图.html');
    }
    modal.hidden = false;
  });
  $('#overlayClose').addEventListener('click', () => { $('#overlayModal').hidden = true; });
  $('#overlayModal').addEventListener('click', e => { if (e.target === $('#overlayModal')) $('#overlayModal').hidden = true; });
  window.addEventListener('keydown', e => { if (e.key === 'Escape') $('#overlayModal').hidden = true; });

  /* ---------- compass ---------- */
  function updateCompass() {
    camera.getWorldDirection(camDir);
    const heading = Math.atan2(camDir.x, -camDir.z);
    const needle = $('#compassNeedle');
    needle.style.transform = 'translateX(-50%) rotate(' + (-heading) + 'rad)';
  }

  /* ---------- UI ---------- */
  const meta = DATA.meta;
  $('#statBuildings').textContent = meta.counts.buildings;
  $('#statArea').textContent = fmt(DATA.school.area, 0);
  $('#dInside').textContent = meta.counts.insideBuildings;
  $('#dOutside').textContent = meta.counts.outsideBuildings;
  $('#dArea').textContent = (DATA.school.area / 10000).toFixed(2) + ' ha';
  $('#dWays').textContent = meta.counts.ways + ' / ' + meta.counts.nodes;
  $('#dSourceSize').textContent = (meta.sourceBytes / 1024).toFixed(1) + ' KB';
  $('#dOrigin').textContent = meta.origin.lat.toFixed(6) + ', ' + meta.origin.lon.toFixed(6);

  function setRangeFill() {
    const input = $('#heightSlider');
    const pct = (Number(input.value) - Number(input.min)) / (Number(input.max) - Number(input.min)) * 100;
    input.style.setProperty('--fill', pct + '%');
  }
  setRangeFill();
  $('#heightSlider').addEventListener('input', e => {
    height = Number(e.target.value);
    $('#heightOut').textContent = height + ' m';
    setRangeFill();
    for (const v of buildingViews) v.group.scale.y = height;
    for (const f of FEATURES) {
      if (f.kind === '建筑') {
        f.y = height + 2.5;
        if (f.labelDef) f.labelDef.y = f.y;
        if (f.edit) {
          f.edit.state.h = height;
          f.edit.initial.h = height;
          f.edit.state.y = 0;
        }
      }
    }
    if (selectedRec) $('#selHeight').textContent = height + ' m（示意）';
    renderer.shadowMap.needsUpdate = true;
  });

  $$('.layers input').forEach(input => {
    input.addEventListener('change', () => {
      const k = input.dataset.layer;
      if (k === 'inside') G.inside.visible = input.checked;
      if (k === 'outside') G.outside.visible = input.checked;
      if (k === 'sports') { G.sports.visible = input.checked; G.track.visible = input.checked; }
      if (k === 'roads') G.roads.visible = input.checked;
      if (k === 'landuse') G.landuse.visible = input.checked;
      if (k === 'context') G.context.visible = input.checked;
      if (k === 'landmarks') G.landmarks.visible = input.checked;
      if (k === 'guide') G.guide.visible = input.checked;
      if (k === 'grid') G.grid.visible = input.checked;
      if (k === 'labels') labelsOn = input.checked;
      if (k === 'codes') codesOn = input.checked;
    });
  });

    /* ---------- copy pose (always available) ---------- */
  let toastTimer = 0;
  function showToast(msg) {
    const t = $('#toast');
    if (!t) return;
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 1800);
  }
  function poseText() {
    const heading = (((-fly.yaw * 180 / Math.PI) % 360) + 360) % 360;
    const pitch = fly.pitch * 180 / Math.PI;
    const lc = worldToLocal(camera.position.x, camera.position.z);
    return 'X ' + lc.x.toFixed(2) + ', Z ' + lc.z.toFixed(2) +
      ', Y ' + camera.position.y.toFixed(2) + ', HDG ' + heading.toFixed(2) + '°, PITCH ' + pitch.toFixed(2) + '°' +
      ' (场地坐标; OSM ' + camera.position.x.toFixed(2) + ', ' + camera.position.z.toFixed(2) + ')' +
      (WALK.active ? ' [第一人称]' : ' [飞行]');
  }
  function copyPose() {
    const txt = poseText();
    const done = () => showToast('已复制：' + txt);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(done).catch(() => { window.prompt('复制坐标 / 角度', txt); });
    } else {
      window.prompt('复制坐标 / 角度', txt);
    }
  }
  $('#copyPose').addEventListener('click', copyPose);
  window.addEventListener('keydown', e => {
    if (e.code !== 'KeyC' || e.ctrlKey || e.metaKey || e.altKey) return;
    const a = document.activeElement;
    if (a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable)) return;
    e.preventDefault();
    copyPose();
  });

$('#clearSelection').addEventListener('click', () => showBuilding(null));
  $('#panelClose').addEventListener('click', () => document.body.classList.remove('panel-open'));
  $('#panelToggle').addEventListener('click', () => document.body.classList.toggle('panel-open'));

  $$('.view-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const v = btn.dataset.view;
      if (v === 'auto') {
        view.auto = !view.auto;
        btn.classList.toggle('active', view.auto);
        return;
      }
      setView(v);
    });
  });

  /* ---------- resize / animate ---------- */
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.fov = phoneLayout() ? 50 : 40;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  const clock = new THREE.Clock();
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
    camera.rotation.set(fly.pitch, fly.yaw, 0, 'YXZ');

    updateCompass();
    updateDebugHud();
    updateLabels();
    renderer.render(scene, camera);
  }

  window.__MODEL = { scene, camera, renderer, view, fly, buildingViews, showBuilding, G, sun, FEATURES, focusFeature, EDIT, setEditorMode, selectEditTarget, exportEdits, importEdits, enterWalk, leaveWalk, copyPose, height: () => height };

  // open in the straightened editor view; the 3D overview remains one click away
  setView('upright');

  try {
    renderer.render(scene, camera);
    requestAnimationFrame(() => {
      loader.classList.add('hidden');
      setTimeout(() => { loader.style.display = 'none'; }, 600);
    });
    animate();
  } catch (err) {
    console.error(err);
    loader.innerHTML = '<b>模型构建失败</b><span style="border:0;animation:none;width:auto;height:auto">' + String(err.message || err) + '</span>';
  }
})();
