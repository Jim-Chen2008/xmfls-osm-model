import * as THREE from 'three';
import { Emitter } from '../utils/emitter.js';

/**
 * 场景容器：渲染器、相机、光照、网格地面、模型根节点。
 * 只负责“画”和“装”，不掺业务逻辑。
 */
export class Viewer extends Emitter {
  constructor(container) {
    super();
    this.container = container;
    this.width = Math.max(1, container.clientWidth);
    this.height = Math.max(1, container.clientHeight);

    /* ---------- 渲染器 ---------- */
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
      stencil: false,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(this.width, this.height, false);
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 0.98;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.domElement.classList.add('viewer-canvas');
    container.appendChild(this.renderer.domElement);

    /* ---------- 场景与相机 ---------- */
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(50, this.width / this.height, 0.2, 6000);
    this.camera.position.set(120, 90, 160);

    /* ---------- 节点分组 ---------- */
    // 模型根节点：导入的 GLB 挂在这里，导出时也只导出这里
    this.modelRoot = new THREE.Group();
    this.modelRoot.name = 'SceneRoot';
    this.scene.add(this.modelRoot);

    // 辅助物（网格、地面、选中框等），永远不参与导出
    this.helperRoot = new THREE.Group();
    this.helperRoot.name = 'Helpers';
    this.scene.add(this.helperRoot);

    this.bounds = new THREE.Box3(new THREE.Vector3(-50, 0, -50), new THREE.Vector3(50, 30, 50));

    this._initLights();
    this._initGround();

    this._clock = new THREE.Clock();
    this._running = false;
    this._onResize = this._onResize.bind(this);

    if (typeof ResizeObserver !== 'undefined') {
      this._ro = new ResizeObserver(() => this._onResize());
      this._ro.observe(container);
    }
    window.addEventListener('resize', this._onResize);
  }

  /* ============ 光照 ============ */
  _initLights() {
    this.hemi = new THREE.HemisphereLight(0xe4eeff, 0xb9ad92, 0.62);
    this.scene.add(this.hemi);

    this.ambient = new THREE.AmbientLight(0xfff7ea, 0.14);
    this.scene.add(this.ambient);

    this.sun = new THREE.DirectionalLight(0xfff0d2, 2.9);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    this.sun.shadow.bias = -0.0006;
    this.sun.shadow.normalBias = 0.06;
    this.sun.shadow.camera.near = 1;
    this.sun.shadow.camera.far = 1200;
    this.scene.add(this.sun);
    this.scene.add(this.sun.target);

    this.fill = new THREE.DirectionalLight(0xd5e4ff, 0.24);
    this.fill.position.set(-1, 0.55, -0.6);
    this.scene.add(this.fill);
  }

  /* ============ 地面 + 网格 ============ */
  _initGround() {
    // 承接阴影的透明地面
    this.ground = new THREE.Mesh(
      new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2),
      new THREE.ShadowMaterial({ color: 0x35301f, opacity: 0.3, transparent: true })
    );
    this.ground.receiveShadow = true;
    this.ground.name = '__shadow_ground';
    this.ground.userData.__nonPickable = true;
    this.ground.renderOrder = -1;
    this.helperRoot.add(this.ground);

    this.gridGroup = new THREE.Group();
    this.gridGroup.name = '__grid';
    this.helperRoot.add(this.gridGroup);
    this._gridSize = 0;
  }

  _rebuildGrid(size, groundY) {
    if (Math.abs(size - this._gridSize) < 0.01 && this.gridGroup.userData.groundY === groundY) return;
    this._gridSize = size;
    this.gridGroup.userData.groundY = groundY;

    // 释放旧网格，避免重复导入模型时泄漏
    for (const child of [...this.gridGroup.children]) {
      child.geometry?.dispose();
      child.material?.dispose();
    }
    this.gridGroup.clear();
    const minorStep = size > 1200 ? 50 : size > 400 ? 10 : 5;
    const majorStep = minorStep * 10;

    const makeGrid = (step, color, opacity) => {
      const divisions = Math.max(2, Math.round(size / step));
      const grid = new THREE.GridHelper(size, divisions, color, color);
      grid.material.transparent = true;
      grid.material.opacity = opacity;
      grid.material.depthWrite = false;
      grid.material.fog = false;
      grid.position.y = groundY;
      return grid;
    };

    this.gridGroup.add(makeGrid(minorStep, 0x8f9a8b, 0.16));
    this.gridGroup.add(makeGrid(majorStep, 0x5f6f61, 0.3));

    const planeSize = size * 1.6;
    this.ground.geometry.dispose();
    this.ground.geometry = new THREE.PlaneGeometry(planeSize, planeSize).rotateX(-Math.PI / 2);
    this.ground.position.y = groundY - 0.01;
  }

  setGridVisible(visible) {
    this.gridGroup.visible = visible;
  }

  setShadowEnabled(enabled) {
    this.renderer.shadowMap.enabled = enabled;
    this.sun.castShadow = enabled;
    this.scene.traverse((obj) => {
      if (obj.isMesh && obj.material) {
        const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
        for (const m of mats) m.needsUpdate = true;
      }
    });
  }

  /**
   * 依据模型包围盒布置光照、网格、阴影相机
   * @param {THREE.Box3} box 有意义内容的包围盒
   * @param {THREE.Box3} full 全场景包围盒（含超大底图）
   */
  applyBounds(box, full) {
    this.bounds = box.clone();
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const radius = Math.max(size.x, size.z, size.y) * 0.5 || 20;

    // 网格：按内容尺寸取整，最小 200m
    const gridSize = Math.max(200, Math.ceil((radius * 2.4) / 50) * 50);
    const groundY = Math.min(0, box.min.y - 0.05);
    this._rebuildGrid(gridSize, groundY);

    // 太阳位置：斜上方，跟随模型中心
    const sunDir = new THREE.Vector3(0.86, 0.66, 0.46).normalize();
    this.sun.position.copy(center).addScaledVector(sunDir, radius * 2.6);
    this.sun.target.position.copy(center);
    this.sun.target.updateMatrixWorld();

    const cam = this.sun.shadow.camera;
    const extent = radius * 1.35;
    cam.left = -extent;
    cam.right = extent;
    cam.top = extent;
    cam.bottom = -extent;
    cam.near = Math.max(0.5, radius * 0.2);
    cam.far = radius * 8 + 200;
    cam.updateProjectionMatrix();
    this.sun.shadow.needsUpdate = true;

    this.fill.position.copy(center).add(new THREE.Vector3(-radius * 2, radius * 1.4, -radius * 1.6));
    this.hemi.position.copy(center).add(new THREE.Vector3(0, radius, 0));

    // 远处地面渐隐，避免 5000m 底图铺满整个画面
    const fogColor = new THREE.Color(0xeae3d2);
    if (this.scene.fog) {
      this.scene.fog.color.copy(fogColor);
      this.scene.fog.near = radius * 3.8;
      this.scene.fog.far = radius * 13;
    } else {
      this.scene.fog = new THREE.Fog(fogColor, radius * 3.8, radius * 13);
    }

    this.emit('bounds', { box: this.bounds, full });
  }

  /** 把导入的模型放进场景 */
  setModel(root) {
    this.clearModel();
    this.modelRoot.add(root);
  }

  clearModel() {
    for (const child of [...this.modelRoot.children]) {
      this.modelRoot.remove(child);
    }
  }

  /* ============ 渲染循环 ============ */
  start(onFrame) {
    if (this._running) return;
    this._running = true;
    this._clock.start();

    const loop = () => {
      if (!this._running) return;
      this._raf = requestAnimationFrame(loop);
      const dt = Math.min(this._clock.getDelta(), 0.1);
      this.frameCount = (this.frameCount || 0) + 1;
      try {
        onFrame?.(dt);
      } catch (err) {
        console.error('[viewer] 帧更新异常', err);
      }
      this.renderer.render(this.scene, this.camera);
      this.emit('afterRender');
    };
    loop();
  }

  stop() {
    this._running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
  }

  _onResize() {
    const w = Math.max(1, this.container.clientWidth);
    const h = Math.max(1, this.container.clientHeight);
    if (w === this.width && h === this.height) return;
    this.width = w;
    this.height = h;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
    this.emit('resize', { width: w, height: h });
  }

  get domElement() {
    return this.renderer.domElement;
  }
}
