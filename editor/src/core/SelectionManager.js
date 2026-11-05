import * as THREE from 'three';
import { TransformControls } from 'three/examples/jsm/controls/TransformControls.js';
import { Emitter } from '../utils/emitter.js';
import { applyTransform, isSameTransform, snapshotTransform } from './History.js';
import { isEffectivelyVisible } from '../utils/helpers.js';

const _box = new THREE.Box3();
const _tmpBox = new THREE.Box3();
const _vec = new THREE.Vector3();
const _quat = new THREE.Quaternion();
const _scale = new THREE.Vector3();
const _mat = new THREE.Matrix4();
const _inv = new THREE.Matrix4();

/**
 * 选中管理：
 *  - 单选 / 多选（Ctrl 追加、Shift 连选）
 *  - 多选时用一个临时轴心（pivot）承载手柄，拖动后按世界矩阵增量分发给每个对象
 *  - 组合 / 解组：把多选变成真正的 Group，之后可像单个对象一样整体变换
 *  - 撤销记录：单对象或多对象变换、组合、解组、隐藏
 */
export class SelectionManager extends Emitter {
  constructor({ viewer, rig, history }) {
    super();
    this.viewer = viewer;
    this.rig = rig;
    this.history = history;
    this.camera = viewer.camera;
    this.dom = viewer.domElement;

    this.selectedList = [];
    this.selected = null; // 主选对象（最后点击的那个）
    this.gizmoMode = 'translate';
    this.gizmoSpace = 'world';
    this.snapEnabled = false;

    this._editSnapshot = null;
    this._multiSnap = null;
    this._pivotSnap = null;
    this._pivotStart = null;
    this._down = null;
    this._gizmoDown = false;

    this.raycaster = new THREE.Raycaster();
    this.pointer = new THREE.Vector2();

    this._initHelpers();
    this._initPivot();
    this._initGizmo();
    this._bindPointer();
  }

  /* ============ 状态 ============ */
  get count() {
    return this.selectedList.length;
  }

  get isMulti() {
    return this.selectedList.length > 1;
  }

  /** 当前被编辑的对象：多选时是轴心，单选时是对象本身 */
  get target() {
    return this.isMulti ? this.pivot : this.selected;
  }

  /* ============ 辅助显示 ============ */
  _initHelpers() {
    this.selectBox = new THREE.Box3Helper(new THREE.Box3(), 0xb4562f);
    this.selectBox.material.transparent = true;
    this.selectBox.material.opacity = 0.95;
    this.selectBox.material.depthTest = false;
    this.selectBox.renderOrder = 3;
    this.selectBox.visible = false;
    this.viewer.scene.add(this.selectBox);

    this.selectAxes = new THREE.AxesHelper(1);
    this.selectAxes.material.transparent = true;
    this.selectAxes.material.opacity = 0.95;
    this.selectAxes.material.depthTest = false;
    this.selectAxes.renderOrder = 3;
    this.selectAxes.visible = false;
    this.viewer.scene.add(this.selectAxes);

    this.hoverBox = new THREE.BoxHelper(new THREE.Object3D(), 0x6f8778);
    this.hoverBox.material.transparent = true;
    this.hoverBox.material.opacity = 0.35;
    this.hoverBox.material.depthTest = false;
    this.hoverBox.renderOrder = 2;
    this.hoverBox.visible = false;
    this.viewer.scene.add(this.hoverBox);
  }

  _initPivot() {
    // 多选的临时轴心，只存在于 scene（不进入模型树、不参与导出）
    this.pivot = new THREE.Group();
    this.pivot.name = '__multi_pivot';
    this.pivot.userData.__nonPickable = true;
    this.viewer.scene.add(this.pivot);
  }

  /* ============ 变换手柄 ============ */
  _initGizmo() {
    this.transform = new TransformControls(this.camera, this.dom);
    this.transform.setSize(0.92);
    this.transform.setSpace(this.gizmoSpace);
    this.transform.setMode(this.gizmoMode);
    this.transform.enabled = false;

    // r169+ 的 TransformControls 不再是 Object3D，需要 add(getHelper())
    this.gizmoObject = typeof this.transform.getHelper === 'function' ? this.transform.getHelper() : this.transform;
    this.gizmoObject.userData.__nonPickable = true;
    this.gizmoObject.visible = false;
    this.viewer.scene.add(this.gizmoObject);

    this.transform.addEventListener('dragging-changed', (event) => {
      if (this.rig.orbit) this.rig.orbit.enabled = !event.value && this.rig.mode === 'edit';
      if (event.value) {
        this.beginEdit();
        this.emit('dragging-start');
      } else {
        this.commitEdit(this._labelForMode());
        this.emit('dragging-end');
      }
      this.emit('dragging', event.value);
    });

    this.transform.addEventListener('objectChange', () => {
      if (this.isMulti) this._applyMultiDelta();
      this.refreshHelpers();
      this.emit('change', this.selected);
    });
  }

  _labelForMode() {
    return { translate: '移动对象', rotate: '旋转对象', scale: '缩放对象' }[this.gizmoMode] || '修改变换';
  }

  /* ============ 指针拾取 ============ */
  _bindPointer() {
    this.dom.addEventListener('pointerdown', (e) => {
      if (e.button !== 0) return;
      this._gizmoDown = this.transform.axis !== null && this.transform.enabled;
      this._down = { x: e.clientX, y: e.clientY, t: performance.now() };
    });

    this.dom.addEventListener('pointerup', (e) => {
      if (e.button !== 0 || !this._down) return;
      const start = this._down;
      this._down = null;
      const moved = Math.hypot(e.clientX - start.x, e.clientY - start.y);
      const elapsed = performance.now() - start.t;
      if (this._gizmoDown) {
        this._gizmoDown = false;
        return;
      }
      if (moved > 5 || elapsed > 700) return;
      if (this.rig.mode !== 'edit') return;

      const additive = e.ctrlKey || e.metaKey || e.shiftKey;
      this.pickAt(e.clientX, e.clientY, { parent: e.altKey, additive });
    });

    let lastHover = 0;
    this.dom.addEventListener('pointermove', (e) => {
      if (this.rig.mode !== 'edit' || this.transform.axis || this._down) return;
      const now = performance.now();
      if (now - lastHover < 70) return;
      lastHover = now;
      const hit = this.raycast(e.clientX, e.clientY);
      if (hit && !this.selectedList.includes(hit.object)) {
        this.hoverBox.setFromObject(hit.object);
        this.hoverBox.visible = true;
        this.dom.style.cursor = 'pointer';
      } else {
        this.hoverBox.visible = false;
        this.dom.style.cursor = '';
      }
    });

    this.dom.addEventListener('pointerleave', () => {
      this.hoverBox.visible = false;
    });
  }

  raycast(clientX, clientY) {
    const rect = this.dom.getBoundingClientRect();
    this.pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hits = this.raycaster.intersectObjects(this.viewer.modelRoot.children, true);
    for (const hit of hits) {
      if (!hit.object.isMesh) continue;
      if (hit.object.userData.__nonPickable) continue;
      if (!isEffectivelyVisible(hit.object)) continue;
      return hit;
    }
    return null;
  }

  pickAt(clientX, clientY, { parent = false, additive = false } = {}) {
    const hit = this.raycast(clientX, clientY);

    if (!hit) {
      if (!additive) this.clear();
      return;
    }

    let target = hit.object;
    if (parent && target.parent && target.parent !== this.viewer.modelRoot) {
      target = target.parent;
    }

    if (additive) {
      this.toggle(target);
      return;
    }
    this.select(target);
  }

  /* ============ 选中 ============ */
  select(object) {
    this.setSelection(object ? [object] : [], object || null);
  }

  setSelection(list, primary = null) {
    const unique = [];
    const seen = new Set();
    for (const obj of list || []) {
      if (!obj || seen.has(obj.uuid)) continue;
      seen.add(obj.uuid);
      unique.push(obj);
    }

    this.selectedList = unique;
    this.selected = primary && unique.includes(primary) ? primary : unique[unique.length - 1] || null;

    this._resetEdit();

    if (this.isMulti) {
      const box = this._unionBox();
      if (!box.isEmpty()) this.pivot.position.copy(box.getCenter(_vec));
      this.pivot.rotation.set(0, 0, 0);
      this.pivot.scale.set(1, 1, 1);
      this.pivot.updateMatrixWorld(true);
      this.transform.attach(this.pivot);
    } else if (this.selected) {
      this.transform.attach(this.selected);
    } else {
      this.transform.detach();
    }

    this.transform.enabled = !!this.selected && this.rig.mode === 'edit';
    this.gizmoObject.visible = !!this.selected;
    this.hoverBox.visible = false;

    this.refreshHelpers();
    this.emit('select', {
      list: [...this.selectedList],
      primary: this.selected,
      multi: this.isMulti,
    });
  }

  toggle(object) {
    if (!object) return;
    if (this.selectedList.includes(object)) {
      const rest = this.selectedList.filter((o) => o !== object);
      this.setSelection(rest, rest[rest.length - 1] || null);
    } else {
      this.setSelection([...this.selectedList, object], object);
    }
  }

  clear() {
    this.setSelection([]);
  }

  selectParent() {
    if (!this.selected) return;
    const parent = this.selected.parent;
    if (parent && parent !== this.viewer.modelRoot) this.select(parent);
  }

  /* ============ 组合 / 解组 ============ */
  groupSelected() {
    const members = this.selectedList.filter((o) => o && o.parent && o !== this.pivot);
    if (members.length < 2) return null;

    const sameParent = members.every((o) => o.parent === members[0].parent);
    const host = sameParent ? members[0].parent : this.viewer.modelRoot;

    // 组节点放在整体中心，之后面板里的“位置”就是这组对象的中心点
    const box = new THREE.Box3();
    for (const obj of members) box.union(new THREE.Box3().setFromObject(obj));
    const center = box.isEmpty() ? new THREE.Vector3() : box.getCenter(new THREE.Vector3());

    const group = new THREE.Group();
    group.name = this._uniqueName(host, '组合');
    group.userData.__combined = true;
    host.updateMatrixWorld(true);
    host.add(group);
    group.position.copy(host.worldToLocal(center.clone()));
    group.updateMatrixWorld(true);
    for (const obj of members) group.attach(obj);
    group.updateMatrixWorld(true);

    this.history.push({
      label: '组合对象',
      undo: () => {
        const parent = group.parent;
        if (!parent) return;
        for (const obj of members) parent.attach(obj);
        parent.remove(group);
        this.viewer.modelRoot.updateMatrixWorld(true);
        this.setSelection(members, members[members.length - 1]);
        this.emit('structure');
      },
      redo: () => {
        host.add(group);
        group.updateMatrixWorld(true);
        for (const obj of members) group.attach(obj);
        group.updateMatrixWorld(true);
        this.setSelection([group], group);
        this.emit('structure');
      },
    });

    this.setSelection([group], group);
    this.emit('structure');
    return group;
  }

  ungroupSelected() {
    const group = this.selected;
    if (!group || group === this.viewer.modelRoot || group.isMesh) return null;
    const parent = group.parent;
    if (!parent || !group.children.length) return null;

    // 只拆一层，子对象保持世界位置
    const members = [...group.children];
    for (const obj of members) parent.attach(obj);
    parent.remove(group);
    this.viewer.modelRoot.updateMatrixWorld(true);

    this.history.push({
      label: '解组',
      undo: () => {
        parent.add(group);
        group.updateMatrixWorld(true);
        for (const obj of members) group.attach(obj);
        group.updateMatrixWorld(true);
        this.setSelection([group], group);
        this.emit('structure');
      },
      redo: () => {
        const p = group.parent || parent;
        for (const obj of members) p.attach(obj);
        p.remove(group);
        this.viewer.modelRoot.updateMatrixWorld(true);
        this.setSelection(members, members[members.length - 1]);
        this.emit('structure');
      },
    });

    this.setSelection(members, members[members.length - 1]);
    this.emit('structure');
    return members;
  }

  _uniqueName(parent, base) {
    const names = new Set(parent.children.map((c) => c.name));
    let i = 1;
    while (names.has(`${base}_${i}`) || names.has(`${base} ${i}`)) i += 1;
    return `${base}_${i}`;
  }

  /* ============ 辅助刷新 ============ */
  _unionBox() {
    const box = new THREE.Box3();
    let has = false;
    for (const obj of this.selectedList) {
      _tmpBox.setFromObject(obj);
      if (_tmpBox.isEmpty()) continue;
      if (!has) {
        box.copy(_tmpBox);
        has = true;
      } else {
        box.union(_tmpBox);
      }
    }
    return box;
  }

  refreshHelpers() {
    if (!this.selectedList.length) {
      this.selectBox.visible = false;
      this.selectAxes.visible = false;
      return;
    }

    const box = this._unionBox();
    if (box.isEmpty()) {
      this.selectBox.visible = false;
      this.selectAxes.visible = false;
      return;
    }

    this.selectBox.box.copy(box);
    this.selectBox.updateMatrixWorld(true);
    this.selectBox.visible = true;
    this.selectAxes.visible = true;

    if (this.isMulti) {
      this.selectAxes.position.copy(this.pivot.position);
      this.selectAxes.quaternion.copy(this.pivot.quaternion);
    } else {
      this.selected.getWorldPosition(_vec);
      this.selected.getWorldQuaternion(_quat);
      this.selectAxes.position.copy(_vec);
      this.selectAxes.quaternion.copy(_quat);
    }

    const size = box.getSize(_scale);
    const axisSize = THREE.MathUtils.clamp(size.length() * 0.22, 0.6, 60);
    this.selectAxes.scale.setScalar(axisSize);
  }

  update() {
    if (this.transform.dragging) this.refreshHelpers();
  }

  /* ============ 编辑事务 ============ */
  beginEdit() {
    if (!this.selected) return;

    if (this.isMulti) {
      this.pivot.updateMatrixWorld(true);
      this._pivotStart = this.pivot.matrixWorld.clone();
      this._pivotSnap = snapshotTransform(this.pivot);
      this._multiSnap = this.selectedList.map((obj) => {
        obj.updateWorldMatrix(true, false);
        return {
          obj,
          world: obj.matrixWorld.clone(),
          parentInv: obj.parent ? obj.parent.matrixWorld.clone().invert() : null,
          local: snapshotTransform(obj),
        };
      });
      return;
    }

    this._editSnapshot = snapshotTransform(this.selected);
  }

  /** 面板在编辑前调用：确保有可回滚的起点 */
  beginEditIfNeeded() {
    if (this.isMulti) {
      if (!this._pivotStart) this.beginEdit();
    } else if (!this._editSnapshot) {
      this.beginEdit();
    }
  }

  /** 把轴心从起始状态到当前状态的世界增量，分发给每个被选对象 */
  _applyMultiDelta() {
    if (!this._multiSnap || !this._pivotStart) return;
    this.pivot.updateMatrixWorld(true);

    _mat.multiplyMatrices(this.pivot.matrixWorld, _inv.copy(this._pivotStart).invert());

    for (const entry of this._multiSnap) {
      const local = new THREE.Matrix4().multiplyMatrices(_mat, entry.world);
      if (entry.parentInv) local.premultiply(entry.parentInv);
      local.decompose(_vec, _quat, _scale);
      entry.obj.position.copy(_vec);
      entry.obj.quaternion.copy(_quat);
      entry.obj.scale.copy(_scale);
      entry.obj.updateMatrix();
    }
    this.viewer.modelRoot.updateMatrixWorld(true);
  }

  commitEdit(label, { mergeKey = null } = {}) {
    if (!this.selected) {
      this._resetEdit();
      return;
    }

    if (this.isMulti) {
      const beforePivot = this._pivotSnap;
      const beforeList = this._multiSnap;
      if (!beforePivot || !beforeList) return;

      const afterPivot = snapshotTransform(this.pivot);
      const afterList = this.selectedList.map((obj) => ({ obj, local: snapshotTransform(obj) }));
      const changed =
        !isSameTransform(beforePivot, afterPivot) ||
        beforeList.some((entry, i) => !isSameTransform(entry.local, afterList[i].local));

      this._resetEdit();
      if (!changed) return;

      const objRefs = beforeList.map((e) => e.obj);
      const restore = (pivotSnap, listSnaps) => {
        applyTransform(this.pivot, pivotSnap);
        objRefs.forEach((obj, i) => {
          if (listSnaps[i]) applyTransform(obj, listSnaps[i]);
        });
        this.viewer.modelRoot.updateMatrixWorld(true);
        this.refreshHelpers();
        this.emit('change', this.selected);
        this.emit('transform-restored', this.selected);
      };

      this.history.pushOrMerge({
        label,
        undo: () => restore(beforePivot, beforeList.map((e) => e.local)),
        redo: () => restore(afterPivot, afterList.map((e) => e.local)),
      }, mergeKey);
      this.emit('commit', { object: this.selected, label, count: objRefs.length });
      return;
    }

    if (!this._editSnapshot) return;
    const object = this.selected;
    const before = this._editSnapshot;
    const after = snapshotTransform(object);
    this._editSnapshot = null;
    if (isSameTransform(before, after)) return;

    this.history.pushOrMerge({
      label: label || '修改变换',
      undo: () => {
        applyTransform(object, before);
        this.emit('transform-restored', object);
        if (object === this.selected) this.refreshHelpers();
      },
      redo: () => {
        applyTransform(object, after);
        this.emit('transform-restored', object);
        if (object === this.selected) this.refreshHelpers();
      },
    }, mergeKey);
    this.emit('commit', { object, label });
  }

  _resetEdit() {
    this._editSnapshot = null;
    this._multiSnap = null;
    this._pivotSnap = null;
    this._pivotStart = null;
  }

  /** 面板输入框直接改数值时使用（多选时作用于轴心） */
  applyTransform(object, patch) {
    if (!object) return;

    if (object === this.pivot) {
      if (patch.position) this.pivot.position.set(patch.position.x, patch.position.y, patch.position.z);
      if (patch.rotation) this.pivot.rotation.set(patch.rotation.x, patch.rotation.y, patch.rotation.z);
      if (patch.scale) {
        this.pivot.scale.set(
          Math.max(0.001, patch.scale.x),
          Math.max(0.001, patch.scale.y),
          Math.max(0.001, patch.scale.z)
        );
      }
      this.pivot.updateMatrix();
      this.pivot.updateMatrixWorld(true);
      this._applyMultiDelta();
    } else {
      if (patch.position) object.position.set(patch.position.x, patch.position.y, patch.position.z);
      if (patch.rotation) object.rotation.set(patch.rotation.x, patch.rotation.y, patch.rotation.z);
      if (patch.scale) {
        object.scale.set(
          Math.max(0.001, patch.scale.x),
          Math.max(0.001, patch.scale.y),
          Math.max(0.001, patch.scale.z)
        );
      }
      object.updateMatrix();
      object.updateMatrixWorld(true);
    }

    this.refreshHelpers();
    this.emit('change', object);
  }

  /* ============ 手柄设置 ============ */
  setGizmoMode(mode) {
    this.gizmoMode = mode;
    this.transform.setMode(mode);
    this.emit('gizmo-mode', mode);
  }

  setGizmoSpace(space) {
    this.gizmoSpace = space;
    this.transform.setSpace(space);
    this.emit('gizmo-space', space);
  }

  setSnapEnabled(enabled) {
    this.snapEnabled = enabled;
    this.transform.setTranslationSnap(enabled ? 0.5 : null);
    this.transform.setRotationSnap(enabled ? THREE.MathUtils.degToRad(15) : null);
    this.transform.setScaleSnap(enabled ? 0.1 : null);
  }

  setGizmoVisible(visible) {
    const active = visible && !!this.selected && this.rig.mode === 'edit';
    this.gizmoObject.visible = visible && !!this.selected;
    this.transform.enabled = active;
  }

  /** 隐藏当前选中对象（可撤销） */
  hideSelected() {
    const objects = [...this.selectedList];
    if (!objects.length) return;
    objects.forEach((o) => {
      o.visible = false;
    });
    this.history.push({
      label: '隐藏对象',
      undo: () => {
        objects.forEach((o) => {
          o.visible = true;
        });
        this.emit('visibility', objects[0]);
      },
      redo: () => {
        objects.forEach((o) => {
          o.visible = false;
        });
        this.emit('visibility', objects[0]);
      },
    });
    this.emit('visibility', objects[0]);
    this.clear();
  }
}
