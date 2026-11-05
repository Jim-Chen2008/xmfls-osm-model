/* 厦门外国语学校（海沧校区）体块模型 · GLB 预览器
   坐标系：原点 = 足球场中心，X 轴 = 球场中线，Z 轴 = 球场长轴，Y 轴向上 */
(function () {
  const $ = (s) => document.querySelector(s);
  const bin = atob(window.__GLB_B64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, logarithmicDepthBuffer: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = .90;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  document.getElementById('stage').appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xebe5da);
  scene.fog = new THREE.Fog(0xebe5da, 1500, 4200);

  const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, .5, 9000);
  camera.position.set(300, 158, 215);

  /* ---------- lights (与网页原版一致) ---------- */
  scene.add(new THREE.HemisphereLight(0xfbf5e9, 0x555a4b, .27));
  const sun = new THREE.DirectionalLight(0xfff2dc, 1.75);
  sun.position.set(-370 + 140, 400, 185 + 40);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.type = THREE.PCFSoftShadowMap;
  const sc = sun.shadow.camera;
  sc.left = -330; sc.right = 330; sc.top = 330; sc.bottom = -330; sc.near = 1; sc.far = 1500;
  sc.updateProjectionMatrix();
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = .08;
  scene.add(sun);
  sun.target.position.set(140, 0, 40);
  scene.add(sun.target);
  const fill = new THREE.DirectionalLight(0xc9d7d1, .13);
  fill.position.set(-247, 220, -310);
  scene.add(fill);
  scene.add(new THREE.AmbientLight(0xf0e9dc, .06));

  /* ---------- helpers: grid + axes + origin ---------- */
  const helpers = new THREE.Group();
  scene.add(helpers);

  const grid = new THREE.GridHelper(400, 40, 0xa9a293, 0xcfc8b8);
  grid.position.y = .03;
  grid.material.transparent = true;
  grid.material.opacity = .34;
  grid.material.depthWrite = false;
  helpers.add(grid);

  function axisLine(a, b, color) {
    const g = new THREE.BufferGeometry().setFromPoints([a, b]);
    const m = new THREE.LineBasicMaterial({ color, transparent: true, opacity: .95, depthTest: false });
    const l = new THREE.Line(g, m);
    l.renderOrder = 999;
    return l;
  }
  helpers.add(axisLine(new THREE.Vector3(-110, .45, 0), new THREE.Vector3(110, .45, 0), 0xc0392b));
  helpers.add(axisLine(new THREE.Vector3(0, .45, -140), new THREE.Vector3(0, .45, 140), 0x2f6fa8));

  const dot = new THREE.Mesh(new THREE.CircleGeometry(1.5, 40), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: .95, side: THREE.DoubleSide }));
  dot.rotation.x = -Math.PI / 2;
  dot.position.y = .5;
  dot.renderOrder = 999;
  helpers.add(dot);

  function labelSprite(text, color, w) {
    const cv = document.createElement('canvas');
    cv.width = 512; cv.height = 128;
    const c = cv.getContext('2d');
    c.fillStyle = 'rgba(252,249,242,.92)';
    c.fillRect(0, 0, 512, 128);
    c.fillStyle = color;
    c.font = '600 62px "Microsoft YaHei", "Noto Sans SC", sans-serif';
    c.textAlign = 'center'; c.textBaseline = 'middle';
    c.fillText(text, 256, 70);
    const t = new THREE.CanvasTexture(cv);
    t.encoding = THREE.sRGBEncoding;
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthTest: false }));
    sp.scale.set(w, w / 4, 1);
    sp.renderOrder = 1000;
    return sp;
  }
  const lx = labelSprite('X 中线', '#c0392b', 18);
  lx.position.set(58, 2.4, 0);
  const lz = labelSprite('Z 长轴', '#2f6fa8', 18);
  lz.position.set(0, 2.4, 78);
  const l0 = labelSprite('0,0', '#3a4238', 8);
  l0.position.set(6, 2.4, 5);
  helpers.add(lx, lz, l0);

  /* ---------- model ---------- */
  const LAYERS = {};
  let baseGround = null;
  let ready = false;

  new THREE.GLTFLoader().parse(bytes.buffer, '', (gltf) => {
    const root = gltf.scene;
    scene.add(root);
    root.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
        if (o.name.indexOf('landuse') >= 0) o.castShadow = false;
        const m = o.material;
        if (m && m.transparent) o.castShadow = false;
        if (o.name.indexOf('base_ground') === 0) { baseGround = o; o.castShadow = false; }
      }
    });
    ['ground', 'landuse', 'sports', 'roads', 'buildings', 'context', 'landmarks'].forEach((n) => {
      const g = root.getObjectByName(n);
      if (g) LAYERS[n] = g;
    });
    ready = true;
    document.getElementById('loader').style.display = 'none';
    setView('iso', true);
  }, (err) => {
    document.getElementById('loader').textContent = '模型解析失败：' + err;
  });

  /* ---------- orbit controls ---------- */
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = .07;
  controls.maxPolarAngle = Math.PI / 2 - .02;
  controls.minDistance = 6;
  controls.maxDistance = 1400;
  controls.target.set(105, 0, 38);

  const VIEWS = {
    iso: { pos: [300, 158, 215], tgt: [105, 0, 38], fov: 45 },
    top: { pos: [168, 800, 42], tgt: [168, 0, 40], fov: 31 },
    pitch: { pos: [52, 78, -124], tgt: [0, 2, 0], fov: 44 },
    gate: { pos: [246, 24, 16], tgt: [292, 5, -30], fov: 44 }
  };

  let tween = null;
  function seek(pos, tgt, fov, ms) {
    const p0 = camera.position.clone(), t0 = controls.target.clone(), f0 = camera.fov;
    tween = { p0, t0, f0, p1: new THREE.Vector3().fromArray(pos), t1: new THREE.Vector3().fromArray(tgt), f1: fov, t0ms: performance.now(), ms: ms };
  }
  function setView(name, instant) {
    const v = VIEWS[name];
    if (!v) return;
    if (instant) {
      camera.position.fromArray(v.pos);
      controls.target.fromArray(v.tgt);
      camera.fov = v.fov; camera.updateProjectionMatrix();
      controls.update();
    } else {
      seek(v.pos, v.tgt, v.fov, 700);
    }
    document.querySelectorAll('.view-btn').forEach((b) => b.classList.toggle('on', b.dataset.view === name));
    document.getElementById('viewName').textContent = ({ iso: '轴测总览', top: '正俯视', pitch: '足球场', gate: '校门' })[name];
  }
  document.querySelectorAll('.view-btn').forEach((b) => b.addEventListener('click', () => setView(b.dataset.view)));
  renderer.domElement.addEventListener('pointerdown', () => { tween = null; });
  renderer.domElement.addEventListener('wheel', () => { tween = null; }, { passive: true });

  /* ---------- layer toggles ---------- */
  document.querySelectorAll('input[data-layer]').forEach((cb) => {
    cb.addEventListener('change', () => {
      const k = cb.dataset.layer;
      if (k === 'helpers') { helpers.visible = cb.checked; return; }
      if (k === 'base') { if (baseGround) baseGround.visible = cb.checked; return; }
      if (LAYERS[k]) LAYERS[k].visible = cb.checked;
    });
  });

  /* ---------- resize / loop ---------- */
  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  const clock = new THREE.Clock();
  function animate() {
    requestAnimationFrame(animate);
    clock.getDelta();
    if (tween) {
      const k = Math.min(1, (performance.now() - tween.t0ms) / tween.ms);
      const e = k < .5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2;
      camera.position.lerpVectors(tween.p0, tween.p1, e);
      controls.target.lerpVectors(tween.t0, tween.t1, e);
      camera.fov = tween.f0 + (tween.f1 - tween.f0) * e;
      camera.updateProjectionMatrix();
      if (k >= 1) tween = null;
    }
    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  window.addEventListener('keydown', (e) => {
    const map = { '1': 'iso', '2': 'top', '3': 'pitch', '4': 'gate' };
    if (map[e.key]) setView(map[e.key]);
  });
  window.__viewer = { setView, camera, controls, scene };
})();
