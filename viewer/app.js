/* 厦门外国语学校 · 大门与喷泉花圃 3D 查看器 */
(function () {
  'use strict';

  const canvas = document.getElementById('c');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.setSize(innerWidth, innerHeight, false);
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.92;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xc9dae9);
  scene.fog = new THREE.Fog(0xc9dae9, 380, 1600);

  const camera = new THREE.PerspectiveCamera(38, innerWidth / innerHeight, 0.5, 20000);

  // 布光：天光 + 斜向阳光 + 补光
  const hemi = new THREE.HemisphereLight(0xdcecff, 0x6a6353, 0.62);
  scene.add(hemi);

  const sun = new THREE.DirectionalLight(0xfff0d8, 1.30);
  sun.position.set(206, 120, 24);
  sun.target.position.set(281, 0, -24);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  const sc = sun.shadow.camera;
  sc.left = -70; sc.right = 70; sc.top = 70; sc.bottom = -70; sc.near = 1; sc.far = 420;
  sc.updateProjectionMatrix();
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.02;
  scene.add(sun); scene.add(sun.target);

  const fill = new THREE.DirectionalLight(0xbcd4ef, 0.55);
  fill.position.set(340, 60, -60);
  scene.add(fill);

  // 坐标换算：Blender(x,y,z) -> three(x, z, -y)
  const P = (x, y, z) => new THREE.Vector3(x, z, -y);

  const VIEWS = {
    street: { pos: P(318, 57, 7.0),  tgt: P(281, 24.5, 6.2), fov: 30 },
    inside: { pos: P(291, -1, 13),   tgt: P(277, 24, 5.2), fov: 42 },
    bed:    { pos: P(267, 11, 6.5),  tgt: P(250.5, -8.5, 0.9), fov: 38 },
    plaza:  { pos: P(215, -28, 18),  tgt: P(266, 10, 3.0), fov: 46 },
    top:    { pos: P(251, -3, 118),  tgt: P(250, -3, 0), fov: 45 }
  };

  let model = null;
  let current = null;
  let anim = null;

  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.maxPolarAngle = Math.PI * 0.495;
  controls.minDistance = 4;
  controls.maxDistance = 900;

  function applyView(name, instant) {
    const v = VIEWS[name];
    if (!v) return;
    current = name;
    document.querySelectorAll('#views button').forEach(b => b.classList.toggle('on', b.dataset.v === name));
    if (instant) {
      camera.position.copy(v.pos);
      controls.target.copy(v.tgt);
      camera.fov = v.fov; camera.updateProjectionMatrix();
      controls.update();
      return;
    }
    anim = {
      t0: performance.now(), dur: 950,
      p0: camera.position.clone(), p1: v.pos.clone(),
      t0v: controls.target.clone(), t1v: v.tgt.clone(),
      f0: camera.fov, f1: v.fov
    };
  }

  function ease(u) { return u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2; }

  // ---------------- 载入模型
  function b64ToBuf(b64) {
    const bin = atob(b64);
    const len = bin.length;
    const buf = new Uint8Array(len);
    for (let i = 0; i < len; i++) buf[i] = bin.charCodeAt(i);
    return buf.buffer;
  }

  const loader = new THREE.GLTFLoader();
  const t0 = performance.now();
  loader.parse(b64ToBuf(window.__MODEL_B64), '', (gltf) => {
    model = gltf.scene;
    model.traverse((o) => {
      if (!o.isMesh) return;
      const n = o.name || '';
      const isHero = /^(GATE_|BED_|FNT_)/.test(n);
      o.castShadow = isHero;
      o.receiveShadow = true;
      if (o.material) {
        const mats = Array.isArray(o.material) ? o.material : [o.material];
        mats.forEach(m => { if (m.map) m.map.anisotropy = 4; });
      }
    });
    scene.add(model);
    // 地面接收阴影（模型的 5km 底板太薄，另外铺一层隐形接影面）
    const ground = new THREE.Mesh(
      new THREE.CircleGeometry(120, 64),
      new THREE.ShadowMaterial({ opacity: 0.18 })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.copy(P(262, 4, 0.03));
    ground.receiveShadow = true;
    scene.add(ground);

    applyView('street', true);
    if (location.hash && VIEWS[location.hash.slice(1)]) applyView(location.hash.slice(1), true);
    const ms = Math.round(performance.now() - t0);
    document.getElementById('loading').classList.add('gone');
    document.getElementById('stat').textContent = '模型载入 ' + ms + ' ms · 拖动查看';
    setTimeout(() => { document.getElementById('loading').style.display = 'none'; }, 700);
  }, (err) => {
    console.error(err);
    document.querySelector('#loading p').textContent = '模型载入失败：' + err;
  });

  // ---------------- 交互
  document.querySelectorAll('#views button').forEach(b => {
    b.addEventListener('click', () => applyView(b.dataset.v));
  });

  const chkShadow = document.getElementById('chkShadow');
  const chkSpin = document.getElementById('chkSpin');
  const chkLabels = document.getElementById('chkLabels');
  const chkRefs = document.getElementById('chkRefs');

  chkShadow.addEventListener('change', () => {
    renderer.shadowMap.enabled = chkShadow.checked;
    sun.castShadow = chkShadow.checked;
    scene.traverse(o => { if (o.isMesh && o.material) o.material.needsUpdate = true; });
  });
  chkSpin.addEventListener('change', () => { controls.autoRotate = chkSpin.checked; controls.autoRotateSpeed = 0.55; });
  chkLabels.addEventListener('change', () => {
    document.querySelectorAll('.lab').forEach(l => l.style.display = chkLabels.checked ? '' : 'none');
  });
  chkRefs.addEventListener('change', () => {
    document.getElementById('refs').classList.toggle('hide', !chkRefs.checked);
  });

  // 参考照片
  const REF = {
    street: ['正立面（街道侧）', '24 m 横墙 + 4 块门墩，金色校名居中，门洞下为推拉门。'],
    gate: ['大门近景（新照片）', '四块门墩 + 通长横墙：左段 / 中门洞 / 右段三段在顶部连成一体。'],
    bed: ['喷泉与花圃（新照片）', '花圃沿喷泉东南侧展开，外缘贴广场椭圆边，球形灌木密植。'],
    aerial: ['俯视实景', '喷泉水池外径约 17.4 m，花圃包住水池东南侧。']
  };
  const refimg = document.getElementById('refimg');
  const refcap = document.getElementById('refcap');
  function setRef(k) {
    if (!window.__REFS || !window.__REFS[k]) return;
    refimg.src = window.__REFS[k];
    refcap.textContent = REF[k][1];
    document.querySelectorAll('#reftabs button').forEach(b => b.classList.toggle('on', b.dataset.r === k));
  }
  document.querySelectorAll('#reftabs button').forEach(b => {
    b.addEventListener('click', () => setRef(b.dataset.r));
  });
  document.getElementById('refsClose').addEventListener('click', () => {
    chkRefs.checked = false;
    document.getElementById('refs').classList.add('hide');
  });
  setRef('gate');

  // 标注
  const LABELS = [
    { el: null, p: P(281.1, 24.5, 10.6), text: '大门 · 中央门洞 + 两侧门卫房 / 高墩 / 端墩' },
    { el: null, p: P(244.3, -8.9, 3.2), text: '喷泉 · 外径 17.4 m' },
    { el: null, p: P(254.0, -13.0, 3.0), text: '花圃 · 球形灌木 + 小乔木' }
  ];
  const labelsBox = document.getElementById('labels');
  LABELS.forEach(L => {
    const d = document.createElement('div');
    d.className = 'lab'; d.textContent = L.text;
    labelsBox.appendChild(d); L.el = d;
  });

  const v = new THREE.Vector3();
  function updateLabels() {
    const show = chkLabels.checked;
    const dist = camera.position.length();
    LABELS.forEach(L => {
      if (!show) { L.el.style.opacity = 0; return; }
      v.copy(L.p).project(camera);
      const behind = v.z > 1;
      const x = (v.x * 0.5 + 0.5) * innerWidth;
      const y = (-v.y * 0.5 + 0.5) * innerHeight;
      const camDist = camera.position.distanceTo(L.p);
      const vis = !behind && camDist < 150 && x > -50 && x < innerWidth + 50 && y > -50 && y < innerHeight + 50;
      L.el.style.opacity = vis ? 1 : 0;
      L.el.style.left = x + 'px';
      L.el.style.top = y + 'px';
    });
  }

  // 键盘
  addEventListener('keydown', (e) => {
    const map = { '1': 'street', '2': 'inside', '3': 'bed', '4': 'plaza', '5': 'top' };
    if (map[e.key]) applyView(map[e.key]);
    if (e.key === 'r' || e.key === 'R') applyView('street');
  });

  addEventListener('resize', () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight, false);
  });

  // 主循环
  let frames = 0, lastT = performance.now(), fps = 0;
  function tick(now) {
    requestAnimationFrame(tick);
    if (anim) {
      const u = Math.min(1, (now - anim.t0) / anim.dur);
      const k = ease(u);
      camera.position.lerpVectors(anim.p0, anim.p1, k);
      controls.target.lerpVectors(anim.t0v, anim.t1v, k);
      camera.fov = anim.f0 + (anim.f1 - anim.f0) * k;
      camera.updateProjectionMatrix();
      if (u >= 1) anim = null;
    }
    controls.update();
    updateLabels();
    renderer.render(scene, camera);

    frames++;
    if (now - lastT > 700) {
      fps = Math.round(frames * 1000 / (now - lastT));
      frames = 0; lastT = now;
      const st = document.getElementById('stat');
      if (model) st.textContent = fps + ' fps · ' + renderer.info.render.triangles.toLocaleString() + ' 三角面';
    }
  }
  requestAnimationFrame(tick);
})();
