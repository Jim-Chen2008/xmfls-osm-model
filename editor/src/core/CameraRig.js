import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Emitter } from '../utils/emitter.js';

const MOVE_KEYS = new Set([
  'KeyW', 'KeyA', 'KeyS', 'KeyD',
  'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight',
  'Space', 'ShiftLeft', 'ShiftRight',
]);

const _forward = new THREE.Vector3();
const _right = new THREE.Vector3();
const _move = new THREE.Vector3();
const _euler = new THREE.Euler(0, 0, 0, 'YXZ');

/**
 * 相机控制：
 *  - 编辑模式：OrbitControls 拖拽环绕 + WASD 推拉平移（Space 上升 / Shift 下降）
 *  - 飞行模式：指针锁定，鼠标移动改变 lookAt 朝向，WASD 自由飞行
 */
export class CameraRig extends Emitter {
  constructor({ camera, domElement, viewer }) {
    super();
    this.camera = camera;
    this.dom = domElement;
    this.viewer = viewer;

    this.mode = 'edit'; // edit | fly | idle
    this.keys = new Set();
    this.flySpeed = 12;
    this.lookSensitivity = 0.0022;
    this.pointerLocked = false;

    this.orbit = new OrbitControls(camera, domElement);
    this.orbit.enableDamping = true;
    this.orbit.dampingFactor = 0.075;
    this.orbit.screenSpacePanning = true;
    this.orbit.rotateSpeed = 0.75;
    this.orbit.zoomSpeed = 0.9;
    this.orbit.panSpeed = 0.85;
    this.orbit.maxPolarAngle = Math.PI * 0.495;
    this.orbit.minDistance = 0.6;
    this.orbit.maxDistance = 4000;
    this.orbit.target.set(0, 0, 0);

    this._yaw = 0;
    this._pitch = 0;
    this._lastOrbitDistance = 30;

    this._bind();
  }

  _bind() {
    this._onKeyDown = (e) => {
      if (this.mode === 'idle') return;
      if (isTypingTarget(e.target)) return;
      if (!MOVE_KEYS.has(e.code)) return;
      if (e.code === 'Space') e.preventDefault();
      this.keys.add(e.code);
    };

    this._onKeyUp = (e) => {
      this.keys.delete(e.code);
    };

    this._onBlur = () => this.keys.clear();

    this._onMouseMove = (e) => {
      if (this.mode !== 'fly' || !this.pointerLocked) return;
      this._yaw -= (e.movementX || 0) * this.lookSensitivity;
      this._pitch -= (e.movementY || 0) * this.lookSensitivity;
      const limit = Math.PI / 2 - 0.02;
      this._pitch = Math.max(-limit, Math.min(limit, this._pitch));
      _euler.set(this._pitch, this._yaw, 0, 'YXZ');
      this.camera.quaternion.setFromEuler(_euler);
    };

    this._onPointerLockChange = () => {
      this.pointerLocked = document.pointerLockElement === this.dom;
      if (!this.pointerLocked && this.mode === 'fly') {
        this.exitFly();
      } else if (this.pointerLocked) {
        this.emit('lock', true);
      }
    };

    window.addEventListener('keydown', this._onKeyDown);
    window.addEventListener('keyup', this._onKeyUp);
    window.addEventListener('blur', this._onBlur);
    document.addEventListener('mousemove', this._onMouseMove);
    document.addEventListener('pointerlockchange', this._onPointerLockChange);

    this.orbit.addEventListener('start', () => {
      this._lastOrbitDistance = this.camera.position.distanceTo(this.orbit.target);
    });
  }

  /* ============ 视角适配 ============ */
  /**
   * 通过把包围盒 8 个角点投影到 NDC 来迭代求取合适距离，
   * 比“包围球 / sin(fov)”更贴合扁平的校园场景。
   */
  _fitDistance(box, dir, fill = 0.84) {
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const corners = [];
    for (let i = 0; i < 8; i += 1) {
      corners.push(new THREE.Vector3(
        i & 1 ? box.max.x : box.min.x,
        i & 2 ? box.max.y : box.min.y,
        i & 4 ? box.max.z : box.min.z
      ));
    }

    const cam = this.camera;
    const savedPos = cam.position.clone();
    const savedQuat = cam.quaternion.clone();

    let dist = Math.max(size.length(), 1);
    for (let i = 0; i < 6; i += 1) {
      cam.position.copy(center).addScaledVector(dir, dist);
      cam.lookAt(center);
      cam.updateMatrixWorld(true);
      let maxNdc = 0;
      for (const c of corners) {
        const p = c.clone().project(cam);
        maxNdc = Math.max(maxNdc, Math.abs(p.x), Math.abs(p.y));
      }
      if (!Number.isFinite(maxNdc) || maxNdc < 1e-4) break;
      const factor = maxNdc / fill;
      dist *= factor;
      if (Math.abs(factor - 1) < 0.01) break;
    }

    cam.position.copy(savedPos);
    cam.quaternion.copy(savedQuat);
    cam.updateMatrixWorld(true);
    return { center, dist };
  }

  fit(box, { animate = false } = {}) {
    if (!box || box.isEmpty()) return;
    const dir = new THREE.Vector3(0.55, 0.62, 0.9).normalize();
    const { center, dist } = this._fitDistance(box, dir, 0.86);
    const size = box.getSize(new THREE.Vector3());
    const radius = Math.max(size.x, size.z) * 0.5 || 20;

    const targetPos = center.clone().addScaledVector(dir, dist);

    this.camera.near = Math.max(0.12, dist / 5000);
    this.camera.far = Math.max(6000, dist * 40);
    this.camera.updateProjectionMatrix();

    this.orbit.minDistance = Math.max(1, radius * 0.02);
    this.orbit.maxDistance = Math.max(400, radius * 20);
    this.orbit.target.copy(center);

    if (animate) {
      this._animateCamera(targetPos, center, 520);
    } else {
      this.camera.position.copy(targetPos);
      this.orbit.update();
    }
    this.flySpeed = THREE.MathUtils.clamp(radius * 0.18, 4, 80);
    this.emit('fit', { box });
  }

  _animateCamera(targetPos, targetLook, duration = 480) {
    const startPos = this.camera.position.clone();
    const startTarget = this.orbit.target.clone();
    const t0 = performance.now();
    const ease = (t) => 1 - Math.pow(1 - t, 3);
    const step = () => {
      const t = Math.min(1, (performance.now() - t0) / duration);
      const k = ease(t);
      this.camera.position.lerpVectors(startPos, targetPos, k);
      this.orbit.target.lerpVectors(startTarget, targetLook, k);
      this.orbit.update();
      if (t < 1) requestAnimationFrame(step);
    };
    step();
  }

  /** 聚焦到某个对象（保留当前视角方向） */
  focusObject(object, opts) {
    const box = new THREE.Box3().setFromObject(object);
    this.focusBox(box, opts);
  }

  /** 聚焦到指定包围盒（多选 / 组合后使用） */
  focusBox(box, { padding = 0.58 } = {}) {
    if (!box || box.isEmpty()) return;

    const dir = this.camera.position.clone().sub(this.orbit.target);
    if (dir.lengthSq() < 1e-6) dir.set(0.6, 0.7, 0.9);
    dir.normalize();

    const { center, dist } = this._fitDistance(box, dir, padding);
    const targetPos = center.clone().addScaledVector(dir, dist);
    this.orbit.target.copy(center);
    this._animateCamera(targetPos, center, 420);
  }

  /* ============ 模式切换 ============ */
  enable() {
    this.mode = 'edit';
    this.orbit.enabled = true;
    this.keys.clear();
    this.emit('mode', 'edit');
  }

  disable() {
    this.mode = 'idle';
    this.orbit.enabled = false;
    this.keys.clear();
    this.emit('mode', 'idle');
  }

  enterFly() {
    if (this.mode === 'fly') return;
    this.mode = 'fly';
    this.orbit.enabled = false;
    this.keys.clear();

    _euler.setFromQuaternion(this.camera.quaternion, 'YXZ');
    this._yaw = _euler.y;
    this._pitch = _euler.x;

    try {
      const p = this.dom.requestPointerLock();
      if (p && typeof p.catch === 'function') p.catch(() => {});
    } catch {
      /* 部分浏览器要求更强的手势，忽略即可 */
    }
    this.emit('mode', 'fly');
  }

  exitFly() {
    if (this.mode !== 'fly') return;
    this.mode = 'edit';
    this.orbit.enabled = true;
    this.keys.clear();
    if (document.pointerLockElement === this.dom) document.exitPointerLock();

    // 让环绕中心落在视线正前方，避免视角突变
    const dir = new THREE.Vector3();
    this.camera.getWorldDirection(dir);
    const dist = Math.max(8, Math.min(120, this._lastOrbitDistance || 30));
    this.orbit.target.copy(this.camera.position).addScaledVector(dir, dist);
    this.orbit.update();
    this.emit('mode', 'edit');
  }

  /* ============ 每帧更新 ============ */
  update(dt) {
    if (this.mode === 'idle') return;

    const speedBase = this.mode === 'fly'
      ? this.flySpeed
      : THREE.MathUtils.clamp(this.camera.position.distanceTo(this.orbit.target) * 0.65, 3, 260);

    let fwd = 0;
    let strafe = 0;
    let vertical = 0;
    if (this.keys.has('KeyW') || this.keys.has('ArrowUp')) fwd += 1;
    if (this.keys.has('KeyS') || this.keys.has('ArrowDown')) fwd -= 1;
    if (this.keys.has('KeyD') || this.keys.has('ArrowRight')) strafe += 1;
    if (this.keys.has('KeyA') || this.keys.has('ArrowLeft')) strafe -= 1;
    if (this.keys.has('Space')) vertical += 1;
    if (this.keys.has('ShiftLeft') || this.keys.has('ShiftRight')) vertical -= 1;

    if (fwd || strafe || vertical) {
      this.camera.getWorldDirection(_forward);
      _right.crossVectors(_forward, this.camera.up).normalize();
      _move.set(0, 0, 0)
        .addScaledVector(_forward, fwd)
        .addScaledVector(_right, strafe);
      _move.y += vertical;
      if (_move.lengthSq() > 0) {
        _move.normalize().multiplyScalar(speedBase * dt);
        this.camera.position.add(_move);
        if (this.mode === 'edit') this.orbit.target.add(_move);
      }
    }

    if (this.mode === 'edit') this.orbit.update();
  }
}

function isTypingTarget(el) {
  if (!el) return false;
  const tag = el.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || el.isContentEditable;
}
