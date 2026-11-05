(async () => {
  const THREE = window.THREE;
  const M = window.__MODEL;
  const G = M.G, scene = M.scene, J = window.OSM_MODEL;

  /* ---------------- 1. football-pitch frame ---------------- */
  function convexHull(points) {
    const pts = points.map(p => [p[0], p[1]]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const lower = [], upper = [];
    for (const p of pts) {
      while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop();
      lower.push(p);
    }
    for (let i = pts.length - 1; i >= 0; i--) {
      const p = pts[i];
      while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop();
      upper.push(p);
    }
    lower.pop(); upper.pop();
    return lower.concat(upper);
  }

  function minAreaRect(points) {
    const H = convexHull(points);
    let best = null;
    for (let i = 0; i < H.length; i++) {
      const q = H[i], r = H[(i + 1) % H.length];
      const ang = Math.atan2(r[1] - q[1], r[0] - q[0]);
      const ca = Math.cos(ang), sa = Math.sin(ang);
      let minU = Infinity, maxU = -Infinity, minV = Infinity, maxV = -Infinity;
      for (const p of H) {
        const u = p[0] * ca + p[1] * sa;
        const v = -p[0] * sa + p[1] * ca;
        if (u < minU) minU = u; if (u > maxU) maxU = u;
        if (v < minV) minV = v; if (v > maxV) maxV = v;
      }
      const area = (maxU - minU) * (maxV - minV);
      if (!best || area < best.area - 1e-9) best = { area, ang, minU, maxU, minV, maxV };
    }
    const cu = (best.minU + best.maxU) / 2, cv = (best.minV + best.maxV) / 2;
    const ca = Math.cos(best.ang), sa = Math.sin(best.ang);
    return {
      cx: cu * ca - cv * sa,
      cz: cu * sa + cv * ca,
      w: best.maxU - best.minU,
      h: best.maxV - best.minV,
      ang: best.ang
    };
  }

  const shiftX = G.sports.position.x, shiftZ = G.sports.position.z;
  const pitchPoly = J.track.inner.polygon.map(p => [p[0] + shiftX, p[1] + shiftZ]);
  const rect = minAreaRect(pitchPoly);
  let longAng = rect.w >= rect.h ? rect.ang : rect.ang + Math.PI / 2;
  if (rect.w < rect.h) { const t = rect.w; rect.w = rect.h; rect.h = t; }

  const ez = new THREE.Vector3(Math.cos(longAng), 0, Math.sin(longAng)).normalize();
  if (ez.z < 0) ez.negate();                        // +Z points towards the southern end of the pitch
  const ex = new THREE.Vector3(ez.z, 0, -ez.x).normalize(); // = up x ez : the halfway-line direction
  const ey = new THREE.Vector3(0, 1, 0);
  const C = new THREE.Vector3(rect.cx, 0, rect.cz);

  const R = new THREE.Matrix4().makeBasis(ex, ey, ez); // pitch frame -> world
  const Rt = R.clone().transpose();                    // world -> pitch frame (rotation only)
  const tShift = C.clone().applyMatrix4(Rt).multiplyScalar(-1);
  const M4 = Rt.clone();
  M4.setPosition(tShift);

  // sanity: the four pitch corners in the new frame
  const corners = pitchPoly.map(p => new THREE.Vector3(p[0], 0, p[1]).applyMatrix4(M4));
  const cxs = corners.map(v => v.x), czs = corners.map(v => v.z);
  const pb = {
    minX: Math.min(...cxs), maxX: Math.max(...cxs),
    minZ: Math.min(...czs), maxZ: Math.max(...czs)
  };

  /* ---------------- 2. line -> ribbon helpers ---------------- */
  const WIDTH_BY_COLOR = {
    '777b72': .70, '9a978c': .45, '3d5849': .50, '4e7058': .45,
    'f5f0e1': .22, 'f4efe1': .18, '41483f': .16, '6d746b': .16,
    '8e8d83': .40, '8e8a7d': .20, '7b5a24': .16
  };

  const up = new THREE.Vector3(0, 1, 0);
  function segmentQuads(a, b, w) {
    const d = new THREE.Vector3().subVectors(b, a);
    const len = d.length();
    if (len < 1e-5) return [];
    const half = w / 2;
    const horiz = Math.hypot(d.x, d.z);
    if (horiz > 1e-4 && Math.abs(d.y) < Math.max(0.02, horiz * 0.02)) {
      const nx = -d.z / horiz * half, nz = d.x / horiz * half;
      const y = (a.y + b.y) / 2 + 0.0015;
      return [[
        new THREE.Vector3(a.x + nx, y, a.z + nz),
        new THREE.Vector3(b.x + nx, y, b.z + nz),
        new THREE.Vector3(b.x - nx, y, b.z - nz),
        new THREE.Vector3(a.x - nx, y, a.z - nz)
      ]];
    }
    const dir = d.clone().normalize();
    const p1 = new THREE.Vector3().crossVectors(dir, up);
    if (p1.lengthSq() < 1e-8) p1.set(1, 0, 0);
    p1.normalize().multiplyScalar(half);
    const p2 = new THREE.Vector3().crossVectors(dir, p1).normalize().multiplyScalar(half);
    return [
      [a.clone().add(p1), b.clone().add(p1), b.clone().sub(p1), a.clone().sub(p1)],
      [a.clone().add(p2), b.clone().add(p2), b.clone().sub(p2), a.clone().sub(p2)]
    ];
  }

  function addQuad(bucket, q) {
    const [p0, p1, p2, p3] = q;
    const n = new THREE.Vector3().subVectors(p1, p0).cross(new THREE.Vector3().subVectors(p2, p0)).normalize();
    for (const v of [p0, p1, p2, p0, p2, p3]) {
      bucket.pos.push(v.x, v.y, v.z);
      bucket.nrm.push(n.x, n.y, n.z);
    }
  }

  function addPolyline(bucket, pts, mode, w, dashed, dashSize, gapSize) {
    const n = pts.length;
    const segs = [];
    if (mode === 'lines') {
      for (let i = 0; i + 1 < n; i += 2) segs.push([pts[i], pts[i + 1]]);
    } else {
      for (let i = 0; i + 1 < n; i++) segs.push([pts[i], pts[i + 1]]);
      if (mode === 'loop' && n > 2) segs.push([pts[n - 1], pts[0]]);
    }
    let phase = 0;
    const cyc = dashSize + gapSize;
    for (const [a, b] of segs) {
      const L = a.distanceTo(b);
      if (L < 1e-5) continue;
      const dir = new THREE.Vector3().subVectors(b, a).divideScalar(L);
      if (!dashed) {
        for (const q of segmentQuads(a, b, w)) addQuad(bucket, q);
      } else {
        let s = 0;
        while (s < L - 1e-6) {
          const cp = (phase + s) % cyc;
          if (cp < dashSize) {
            const run = Math.min(dashSize - cp, L - s);
            const q0 = a.clone().addScaledVector(dir, s);
            const q1 = a.clone().addScaledVector(dir, s + run);
            for (const q of segmentQuads(q0, q1, w)) addQuad(bucket, q);
            s += run;
          } else {
            s += Math.min(cyc - cp, L - s);
          }
        }
        phase = (phase + L) % cyc;
      }
    }
  }

  /* ---------------- 3. build the export graph ---------------- */
  scene.updateMatrixWorld(true);

  const root = new THREE.Group();
  root.name = 'XWFLS_Haicang';

  const layerDefs = [
    ['ground', G.ground],
    ['landuse', G.landuse],
    ['sports', G.sports],
    ['roads', G.roads],
    ['buildings', G.inside],
    ['context', G.context],
    ['landmarks', G.landmarks]
  ];

  const stats = { meshes: 0, lines: 0, tris: 0, skipped: [] };
  const specialNames = new Map();
  if (G.sports.children[0]) specialNames.set(G.sports.children[0], 'track_surface');
  if (G.sports.children[1]) specialNames.set(G.sports.children[1], 'pitch_football_surface');
  if (G.sports.children[2]) specialNames.set(G.sports.children[2], 'pitch_football_touchline');

  // named feature groups (basketball courts, gate, fountain, ...) -> readable mesh names
  const groupNames = new Map();
  for (const f of M.FEATURES || []) {
    if (f && f.group) groupNames.set(f.group, f.short || f.name);
  }
  function ancestorName(o) {
    let p = o.parent;
    while (p) {
      if (groupNames.has(p)) return groupNames.get(p);
      p = p.parent;
    }
    return null;
  }

  for (const [layerName, group] of layerDefs) {
    const layer = new THREE.Group();
    layer.name = layerName;
    const buckets = new Map();
    let idx = 0;

    group.traverse(o => {
      if (o === group) return;
      if (!(o.isMesh || o.isLine)) return;
      if (o.visible === false) return;
      const gp = o.geometry && o.geometry.parameters;
      const isBackdrop = !!(o.isMesh && gp && gp.width === 5000 && gp.height === 5000);

      const Tm = new THREE.Matrix4().multiplyMatrices(M4, o.matrixWorld);
      idx++;

      if (o.isMesh) {
        const geo = o.geometry.clone();
        geo.applyMatrix4(Tm);
        const mesh = new THREE.Mesh(geo, o.material);
        const rec = o.userData && o.userData.building;
        const base = isBackdrop ? 'base_ground_5000m'
          : (specialNames.get(o) ||
            (rec ? ('building_' + rec.id) : (ancestorName(o) || (layerName + '_mesh'))));
        mesh.name = base + '_' + idx;
        layer.add(mesh);
        stats.meshes++;
        const pos = geo.attributes.position;
        stats.tris += pos ? pos.count / 3 : 0;
        return;
      }

      const posAttr = o.geometry.attributes.position;
      const pts = [];
      for (let i = 0; i < posAttr.count; i++) {
        pts.push(new THREE.Vector3().fromBufferAttribute(posAttr, i).applyMatrix4(Tm));
      }
      const mat = o.material;
      const w = WIDTH_BY_COLOR[(mat.color ? mat.color.getHexString() : '')] || .25;
      const dashed = !!mat.isLineDashedMaterial;
      const key = (mat.color ? mat.color.getHexString() : 'fff') + '|' +
        (mat.transparent ? 't' : 'o') + '|' + (mat.opacity === undefined ? 1 : mat.opacity);
      if (!buckets.has(key)) {
        const rm = new THREE.MeshStandardMaterial({
          color: mat.color ? mat.color.clone() : new THREE.Color(0xffffff),
          roughness: .92,
          metalness: 0,
          side: THREE.DoubleSide,
          transparent: (mat.opacity !== undefined && mat.opacity < 1) || !!mat.transparent,
          opacity: mat.opacity === undefined ? 1 : mat.opacity
        });
        rm.name = 'linework_' + key.replace(/\|/g, '_');
        buckets.set(key, { mat: rm, pos: [], nrm: [], n: 0 });
      }
      const b = buckets.get(key);
      const mode = o.isLineSegments ? 'lines' : (o.isLineLoop ? 'loop' : 'strip');
      addPolyline(b, pts, mode, w, dashed, mat.dashSize || 5, mat.gapSize || 4);
      b.n++;
      stats.lines++;
    });

    for (const [, b] of buckets) {
      if (!b.pos.length) continue;
      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.Float32BufferAttribute(b.pos, 3));
      geo.setAttribute('normal', new THREE.Float32BufferAttribute(b.nrm, 3));
      const mesh = new THREE.Mesh(geo, b.mat);
      mesh.name = 'linework_' + b.mat.color.getHexString() + '_x' + b.n;
      layer.add(mesh);
      stats.tris += b.pos.length / 9;
    }
    root.add(layer);
  }

  root.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(root);

  /* ---------------- 4. export ---------------- */
  const exporter = new THREE.GLTFExporter();
  const buffer = await new Promise((resolve, reject) => {
    try {
      exporter.parse(root, resolve, { binary: true, onlyVisible: true, embedImages: true });
    } catch (e) { reject(e); }
  });

  const bytes = new Uint8Array(buffer);
  let bin = '';
  const CH = 0x8000;
  for (let i = 0; i < bytes.length; i += CH) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, Math.min(i + CH, bytes.length)));
  }
  window.__GLB_B64 = btoa(bin);

  return {
    glbBytes: bytes.length,
    pitch: {
      center: { x: rect.cx, z: rect.cz },
      sizeAlongX: pb.maxX - pb.minX,
      sizeAlongZ: pb.maxZ - pb.minZ,
      minX: pb.minX, maxX: pb.maxX, minZ: pb.minZ, maxZ: pb.maxZ,
      longAxisWorldAzimuthDeg: Math.atan2(ez.z, ez.x) * 180 / Math.PI
    },
    bounds: {
      min: [box.min.x, box.min.y, box.min.z],
      max: [box.max.x, box.max.y, box.max.z]
    },
    stats,
    objects: root.children.map(c => c.name + ':' + c.children.length)
  };
})();
