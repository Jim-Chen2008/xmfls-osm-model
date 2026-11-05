import * as THREE from 'three';
import { Emitter } from '../utils/emitter.js';

const DOWN = new THREE.Vector3(0, -1, 0);
const _euler = new THREE.Euler(0, 0, 0, 'YXZ');
const _fwd = new THREE.Vector3();
const _right = new THREE.Vector3();
const _wish = new THREE.Vector3();

/**
 * 第一人称漫游：
 *  - 指针锁定后鼠标改变朝向
 *  - W/A/S/D 水平行走，Shift 奔跑，Space 跳跃
 *  - 每帧向下射线检测地面高度，重力把玩家压到地面（起坡/上台阶自动贴合）
 */
export class FirstPerson extends Emitter {
  constructor({ camera, viewer, domElement }) {
    super();
    this.camera = camera;
    this.viewer = viewer;
    this.dom = domElement;

    this.active = false;
    this.pointerLocked = false;

    this.eyeHeight = 1.68;
    this.walkSpeed = 3.6;
    this.runSpeed = 7.2;
    this.gravity = 22;
    this.jumpSpeed = 6.2;
    this.stepHeight = 0.65;

    this.position = new THREE.Vector3(0, this.eyeHeight, 0);
    this.velocityY = 0;
    this.horizontal = new THREE.Vector3();
    this.grounded = true;
    this.bobPhase = 0;

    this.yaw = 0;
    this.pitch = 0;
    this.keys = new Set();
    this.raycaster = new THREE.Raycaster();
    this.raycaster.far = 3000;

    this._bind();
  }

  _bind() {
    this._onMouseMove = (e) => {
      if (!this.active || !this.pointerLocked) return;
      this.yaw -= (e.movementX || 0) * 0.0022;
      this.pitch -= (e.movementY || 0) * 0.0022;
      const limit = Math.PI / 2 - 0.03;
      this.pitch = Math.max(-limit, Math.min(limit, this.pitch));
      this._applyLook();
    };

    this._onKeyDown = (e) => {
      if (!this.active) return;
      const code = e.code;
      if (code === 'Space') {
        e.preventDefault();
        if (this.grounded) {
          this.velocityY = this.jumpSpeed;
          this.grounded = false;
        }
        this.keys.add(code);
        return;
      }
      if (['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ShiftLeft', 'ShiftRight'].includes(code)) {
        this.keys.add(code);
      }
    };

    this._onKeyUp = (e) => this.keys.delete(e.code);

    this._onLockChange = () => {
      this.pointerLocked = document.pointerLockElement === this.dom;
      this.emit('lock', this.pointerLocked);
      if (!this.pointerLocked && this.active) this.exit();
    };

    this._onClick = () => {
      if (this.active && !this.pointerLocked) this._requestLock();
    };

    document.addEventListener('mousemove', this._onMouseMove);
    document.addEventListener('pointerlockchange', this._onLockChange);
    window.addEventListener('keydown', this._onKeyDown);
    window.addEventListener('keyup', this._onKeyUp);
    this.dom.addEventListener('click', this._onClick);
  }

  _requestLock() {
    try {
      const p = this.dom.requestPointerLock();
      if (p && typeof p.catch === 'function') p.catch(() => {});
    } catch {
      /* ignore */
    }
  }

  _applyLook() {
    _euler.set(this.pitch, this.yaw, 0, 'YXZ');
    this.camera.quaternion.setFromEuler(_euler);
  }

  /**
   * 向下打射线取地面高度
   * @returns {number} 地面 Y；没有命中返回 -Infinity
   */
  sampleGround(x, z, fromY) {
    const startY = Number.isFinite(fromY) ? fromY : this.viewer.bounds.max.y + 60;
    this.raycaster.set(new THREE.Vector3(x, startY, z), DOWN);
    this.raycaster.far = Math.max(60, startY + 200);
    const hits = this.raycaster.intersectObject(this.viewer.modelRoot, true);
    for (const hit of hits) {
      if (!hit.object.isMesh || !hit.object.visible) continue;
      if (this._ancestorsVisible(hit.object)) return hit.point.y;
    }
    return -Infinity;
  }

  _ancestorsVisible(obj) {
    let cur = obj;
    while (cur && cur !== this.viewer.modelRoot) {
      if (!cur.visible) return false;
      cur = cur.parent;
    }
    return true;
  }

  /**
   * @param {{x?:number, z?:number, yaw?:number}} [spawn] 指定落地点（默认在相机位置）
   */
  enter(spawn = null) {
    if (this.active) return;

    const useSpawn = spawn && Number.isFinite(spawn.x) && Number.isFinite(spawn.z);
    const from = useSpawn
      ? new THREE.Vector3(spawn.x, 0, spawn.z)
      : this.camera.position.clone();

    const ground = this.sampleGround(from.x, from.z, this.camera.position.y + 2);
    const feetY = Number.isFinite(ground) ? ground : 0;

    this.position.set(from.x, feetY + this.eyeHeight, from.z);
    this.velocityY = 0;
    this.horizontal.set(0, 0, 0);
    this.keys.clear();
    this.grounded = true;

    if (useSpawn && Number.isFinite(spawn.yaw)) {
      this.yaw = spawn.yaw;
      this.pitch = 0;
    } else {
      _euler.setFromQuaternion(this.camera.quaternion, 'YXZ');
      this.yaw = _euler.y;
      this.pitch = THREE.MathUtils.clamp(_euler.x, -0.55, 0.3);
    }

    // 相机进入人眼高度，fov 略带广角，行走更有临场感
    this.camera.fov = 68;
    this.camera.near = 0.05;
    this.camera.updateProjectionMatrix();
    this.camera.position.copy(this.position);
    this._applyLook();

    this.active = true;
    this._requestLock();
    this.emit('enter');
  }

  exit() {
    if (!this.active) return;
    this.active = false;
    this.keys.clear();
    this.horizontal.set(0, 0, 0);
    if (document.pointerLockElement === this.dom) document.exitPointerLock();
    this.camera.fov = 50;
    this.camera.near = 0.15;
    this.camera.updateProjectionMatrix();
    this.emit('exit');
  }

  update(dt) {
    if (!this.active) return;

    const running = this.keys.has('ShiftLeft') || this.keys.has('ShiftRight');
    const speed = running ? this.runSpeed : this.walkSpeed;

    let fwd = 0;
    let strafe = 0;
    if (this.keys.has('KeyW') || this.keys.has('ArrowUp')) fwd += 1;
    if (this.keys.has('KeyS') || this.keys.has('ArrowDown')) fwd -= 1;
    if (this.keys.has('KeyD') || this.keys.has('ArrowRight')) strafe += 1;
    if (this.keys.has('KeyA') || this.keys.has('ArrowLeft')) strafe -= 1;

    _fwd.set(-Math.sin(this.yaw), 0, -Math.cos(this.yaw));
    _right.set(Math.cos(this.yaw), 0, -Math.sin(this.yaw));

    _wish.set(0, 0, 0);
    if (fwd || strafe) {
      _wish.addScaledVector(_fwd, fwd).addScaledVector(_right, strafe).normalize().multiplyScalar(speed);
    }

    // 水平速度平滑，避免生硬启停
    const k = 1 - Math.exp(-14 * dt);
    this.horizontal.lerp(_wish, k);

    const feetY = this.position.y - this.eyeHeight;
    const nextX = this.position.x + this.horizontal.x * dt;
    const nextZ = this.position.z + this.horizontal.z * dt;

    // 台阶/墙体判定：目标点地面高出脚底太多就不让过去（体块模型近似为实体）
    const nextGround = this.sampleGround(nextX, nextZ, this.position.y + 0.4);
    const allow = !Number.isFinite(nextGround) || nextGround - feetY <= this.stepHeight;
    if (allow) {
      this.position.x = nextX;
      this.position.z = nextZ;
    } else {
      this.horizontal.multiplyScalar(0.25);
    }

    // 重力 + 地面吸附
    this.velocityY -= this.gravity * dt;
    this.position.y += this.velocityY * dt;

    const groundY = this.sampleGround(this.position.x, this.position.z, this.position.y + 0.4);
    const floor = Number.isFinite(groundY) ? groundY : 0;
    if (this.position.y <= floor + this.eyeHeight) {
      this.position.y = floor + this.eyeHeight;
      this.velocityY = 0;
      this.grounded = true;
    } else {
      this.grounded = false;
    }

    // 走动时轻微的步伐起伏
    const planarSpeed = Math.hypot(this.horizontal.x, this.horizontal.z);
    if (this.grounded && planarSpeed > 0.4) {
      this.bobPhase += dt * (running ? 13 : 9);
    } else {
      this.bobPhase += dt * 2;
    }
    const bob = this.grounded ? Math.sin(this.bobPhase) * Math.min(0.035, planarSpeed * 0.006) : 0;

    this.camera.position.set(this.position.x, this.position.y + bob, this.position.z);
    this._applyLook();

    // 掉出世界时兜底
    if (this.position.y < -500) {
      this.position.set(0, 50, 0);
      this.velocityY = 0;
    }
  }
}
