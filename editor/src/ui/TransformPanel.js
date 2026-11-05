import * as THREE from 'three';
import { copyText, fmt, normalizeDeg, collectStats, compactNumber, throttle } from '../utils/helpers.js';
import { toast } from './Toast.js';

const COPY_ICON = '<svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M15 6.5V5.2A1.7 1.7 0 0 0 13.3 3.5H5.2A1.7 1.7 0 0 0 3.5 5.2v8.1A1.7 1.7 0 0 0 5.2 15H6.5"/></svg>';
const CHECK_ICON = '<svg viewBox="0 0 24 24" width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7"/></svg>';
const STEP_UP = '<svg viewBox="0 0 10 6" width="9" height="5"><path d="M5 0.6 9.4 6H0.6z" fill="currentColor"/></svg>';
const STEP_DOWN = '<svg viewBox="0 0 10 6" width="9" height="5"><path d="M5 5.4 0.6 0h8.8z" fill="currentColor"/></svg>';

const RAD2DEG = 180 / Math.PI;
const DEG2RAD = Math.PI / 180;

const GROUPS = [
  { key: 'position', label: '位置', unit: 'm', step: 0.1, digits: 3 },
  { key: 'rotation', label: '旋转', unit: '°', step: 1, digits: 2 },
  { key: 'scale', label: '缩放', unit: '×', step: 0.01, digits: 3 },
];

/**
 * 对象变换面板：
 *  - 位置 / 旋转 / 缩放三组数值，可输入、可用 ▲▼ 步进、可逐值复制
 *  - 单选时编辑对象本身；多选时编辑整体轴心（块），所有成员一起变化
 */
export class TransformPanel {
  constructor({ container, selection, elements }) {
    this.container = container;
    this.selection = selection;
    this.el = elements; // { name, path, badge, meta, actions: {...} }
    this.inputs = new Map(); // `${group}.${axis}` -> input
    this.currentList = [];
    this._stepping = false;
    this._stepTimer = null;

    this._buildRows();
    this._bind();

    this.refreshMeta = throttle(() => this._refreshMeta(), 160);
  }

  _buildRows() {
    this.container.innerHTML = '';
    for (const group of GROUPS) {
      const wrap = document.createElement('div');
      wrap.className = 'tgroup';
      wrap.dataset.group = group.key;

      const head = document.createElement('div');
      head.className = 'tgroup-head';
      head.innerHTML = `<span>${group.label}</span><em>${group.unit}</em>`;

      const copyAll = document.createElement('button');
      copyAll.type = 'button';
      copyAll.className = 'copy-all';
      copyAll.textContent = '复制全部';
      copyAll.title = `复制${group.label}的 X / Y / Z`;
      head.appendChild(copyAll);

      const fields = document.createElement('div');
      fields.className = 'fields';

      for (const axis of ['x', 'y', 'z']) {
        const field = document.createElement('div');
        field.className = 'field';
        field.dataset.axis = axis;

        const ax = document.createElement('span');
        ax.className = 'ax';
        ax.textContent = axis.toUpperCase();

        const input = document.createElement('input');
        input.type = 'number';
        input.step = String(group.step);
        input.dataset.group = group.key;
        input.dataset.axis = axis;
        input.dataset.digits = String(group.digits);
        input.value = '0';
        input.disabled = true;
        input.setAttribute('aria-label', `${group.label} ${axis.toUpperCase()}`);

        // 上下步进箭头
        const stepper = document.createElement('div');
        stepper.className = 'stepper';
        stepper.title = `点按步进 ${group.step}${group.unit}（按住 Shift ×10，可长按连续调整）`;
        for (const [dir, icon, label] of [['1', STEP_UP, '增加'], ['-1', STEP_DOWN, '减少']]) {
          const b = document.createElement('button');
          b.type = 'button';
          b.className = 'step-btn';
          b.dataset.dir = dir;
          b.tabIndex = -1;
          b.setAttribute('aria-label', `${label}${group.label} ${axis.toUpperCase()}`);
          b.innerHTML = icon;
          stepper.appendChild(b);
        }

        const cp = document.createElement('button');
        cp.type = 'button';
        cp.className = 'cp';
        cp.title = '复制该数值';
        cp.innerHTML = COPY_ICON;

        field.append(ax, input, stepper, cp);
        fields.appendChild(field);
        this.inputs.set(`${group.key}.${axis}`, input);
      }

      wrap.append(head, fields);
      this.container.appendChild(wrap);

      copyAll.addEventListener('click', () => {
        const obj = this.selection.target;
        if (!obj) return;
        const values = ['x', 'y', 'z'].map((a) => this._readValue(obj, group.key, a));
        this._copy(`${fmt(values[0], group.digits)}, ${fmt(values[1], group.digits)}, ${fmt(values[2], group.digits)}`);
      });
    }
  }

  _bind() {
    const body = this.container;

    body.addEventListener('pointerdown', (e) => {
      const step = e.target.closest('.step-btn');
      if (step) {
        e.preventDefault();
        e.stopPropagation();
        this._startStepping(step, e);
        return;
      }
      if (e.target.closest('.cp')) e.preventDefault();
    });

    body.addEventListener('click', async (e) => {
      const btn = e.target.closest('.cp');
      if (!btn) return;
      const field = btn.closest('.field');
      const input = field?.querySelector('input');
      if (!input) return;
      const digits = Number(input.dataset.digits || 3);
      const raw = parseFloat(input.value);
      this._copy(fmt(Number.isFinite(raw) ? raw : 0, digits), btn);
    });

    body.addEventListener('focusin', (e) => {
      const input = e.target.closest('input');
      if (!input) return;
      this.selection.beginEdit();
      input.select?.();
    });

    body.addEventListener('input', (e) => {
      const input = e.target.closest('input');
      if (!input) return;
      const value = parseFloat(input.value);
      if (!Number.isFinite(value)) return;
      this._apply(input, value);
    });

    const commit = (e) => {
      const input = e.target.closest?.('input');
      if (!input) return;
      this.selection.commitEdit();
      this.refresh();
    };
    body.addEventListener('change', commit);
    body.addEventListener('focusout', commit);

    body.addEventListener('keydown', (e) => {
      const input = e.target.closest('input');
      if (!input) return;
      if (e.key === 'Enter') {
        input.blur();
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
        e.preventDefault();
        const step = parseFloat(input.step) || 0.1;
        const dir = e.key === 'ArrowUp' ? 1 : -1;
        const mult = e.shiftKey ? 10 : 1;
        const value = (parseFloat(input.value) || 0) + step * dir * mult;
        input.value = value.toFixed(Number(input.dataset.digits || 3));
        this._apply(input, value);
        this.selection.commitEdit(undefined, {
          mergeKey: `step:${this.selection.target?.uuid}:${input.dataset.group}.${input.dataset.axis}`,
        });
      }
    });
  }

  /* ============ 上下步进 ============ */
  _startStepping(btn, downEvent) {
    const field = btn.closest('.field');
    const input = field?.querySelector('input');
    if (!input || input.disabled) return;

    const dir = Number(btn.dataset.dir) || 1;
    const step = parseFloat(input.step) || 0.1;
    const digits = Number(input.dataset.digits || 3);
    const mult = downEvent.shiftKey ? 10 : 1;

    if (!this._stepping) {
      this.selection.beginEdit();
      this._stepping = true;
    }

    const applyStep = () => {
      const current = parseFloat(input.value);
      const value = (Number.isFinite(current) ? current : 0) + step * dir * mult;
      input.value = value.toFixed(digits);
      this._apply(input, value);
    };

    applyStep();

    const mergeKey = `step:${this.selection.target?.uuid}:${input.dataset.group}.${input.dataset.axis}`;

    // 按住 0.35s 后开始连续步进
    const delay = setTimeout(() => {
      this._stepTimer = setInterval(applyStep, 80);
    }, 350);

    const stop = () => {
      clearTimeout(delay);
      if (this._stepTimer) clearInterval(this._stepTimer);
      this._stepTimer = null;
      document.removeEventListener('pointerup', stop);
      document.removeEventListener('pointercancel', stop);
      if (!this._stepping) return;
      this._stepping = false;
      this.selection.commitEdit(undefined, { mergeKey });
      this.refresh();
    };

    document.addEventListener('pointerup', stop);
    document.addEventListener('pointercancel', stop);
  }

  async _copy(text, btn) {
    const ok = await copyText(text);
    if (!ok) {
      toast('复制失败，请手动选择文本复制', 'error');
      return;
    }
    if (btn) {
      const original = btn.innerHTML;
      btn.innerHTML = CHECK_ICON;
      btn.classList.add('done');
      setTimeout(() => {
        btn.innerHTML = original;
        btn.classList.remove('done');
      }, 900);
    }
  }

  _readValue(obj, group, axis) {
    if (group === 'rotation') return normalizeDeg(obj.rotation[axis] * RAD2DEG);
    return obj[group][axis];
  }

  _apply(input, value) {
    const obj = this.selection.target;
    if (!obj) return;
    this.selection.beginEditIfNeeded();
    const group = input.dataset.group;
    const axis = input.dataset.axis;
    const digits = Number(input.dataset.digits || 3);

    if (group === 'rotation') {
      const deg = {
        x: normalizeDeg(obj.rotation.x * RAD2DEG),
        y: normalizeDeg(obj.rotation.y * RAD2DEG),
        z: normalizeDeg(obj.rotation.z * RAD2DEG),
      };
      deg[axis] = value;
      obj.rotation.set(deg.x * DEG2RAD, deg.y * DEG2RAD, deg.z * DEG2RAD);
    } else if (group === 'scale') {
      obj.scale[axis] = Math.max(0.001, Number(value.toFixed(Math.max(digits, 3))));
    } else {
      obj.position[axis] = value;
    }

    obj.updateMatrix();
    obj.updateMatrixWorld(true);
    this.selection.applyTransform(obj, {});
  }

  /* ============ 与选中同步 ============ */
  setSelection(list, primary) {
    this.currentList = list || [];
    const has = this.currentList.length > 0;
    const multi = this.currentList.length > 1;
    const obj = primary || this.currentList[0] || null;

    if (!has) {
      this.el.name.textContent = '在视口中点击任意对象以选中';
      this.el.name.classList.add('empty');
      this.el.path.textContent = 'Ctrl / Shift + 点击 可多选后组合';
      this.el.badge.textContent = '未选中';
      this.el.badge.classList.add('off');
      this.el.meta.textContent = '';
    } else if (multi) {
      this.el.name.textContent = `已选 ${this.currentList.length} 个对象`;
      this.el.name.classList.remove('empty');
      const names = this.currentList.slice(0, 3).map((o) => o.name || '(未命名)').join('、');
      this.el.path.textContent = this.currentList.length > 3 ? `${names} 等` : names;
      this.el.badge.textContent = `多选 ${this.currentList.length}`;
      this.el.badge.classList.remove('off');
    } else {
      this.el.name.textContent = obj.name || '(未命名)';
      this.el.name.classList.remove('empty');
      this.el.path.textContent = this._pathOf(obj);
      this.el.badge.textContent = '已选中';
      this.el.badge.classList.remove('off');
    }

    for (const input of this.inputs.values()) {
      input.disabled = !has;
      input.placeholder = has ? '0' : '—';
      if (!has) input.value = '';
    }
    this.container.setAttribute('aria-disabled', String(!has));

    const a = this.el.actions || {};
    if (a.parent) a.parent.disabled = !has || multi;
    if (a.focus) a.focus.disabled = !has;
    if (a.exportSelected) a.exportSelected.disabled = !has || multi;
    if (a.group) a.group.disabled = !multi;
    if (a.ungroup) {
      const g = !multi ? obj : null;
      a.ungroup.disabled = !(g && !g.isMesh && g.children && g.children.length > 0);
    }

    if (has) {
      this.refresh();
      this._refreshMeta();
    }
  }

  /** 读取当前被编辑对象（多选时为轴心）的数值 */
  refresh() {
    const obj = this.selection.target;
    if (!obj) return;

    const active = document.activeElement;
    for (const group of GROUPS) {
      for (const axis of ['x', 'y', 'z']) {
        const input = this.inputs.get(`${group.key}.${axis}`);
        if (!input || input === active) continue;
        const value = this._readValue(obj, group.key, axis);
        input.value = fmt(value, group.digits);
      }
    }
    this.refreshMeta();
  }

  _refreshMeta() {
    const obj = this.selection.target;
    if (!obj) return;

    if (this.currentList.length > 1) {
      const box = new THREE.Box3();
      let stats = { triangles: 0, materials: 0 };
      for (const o of this.currentList) {
        box.union(new THREE.Box3().setFromObject(o));
        const s = collectStats(o);
        stats = { triangles: stats.triangles + s.triangles, materials: stats.materials + s.materials };
      }
      const size = box.isEmpty() ? new THREE.Vector3() : box.getSize(new THREE.Vector3());
      this.el.meta.innerHTML = [
        `整体范围 <b>${fmt(size.x, 2)} × ${fmt(size.y, 2)} × ${fmt(size.z, 2)}</b> m`,
        `对象 <b>${this.currentList.length}</b> · 三角面 <b>${compactNumber(stats.triangles)}</b>`,
        '组合后即可作为一个整体继续编辑',
      ].join('<br>');
      return;
    }

    const world = new THREE.Vector3();
    obj.getWorldPosition(world);
    const box = new THREE.Box3().setFromObject(obj);
    const size = box.isEmpty() ? new THREE.Vector3() : box.getSize(new THREE.Vector3());
    const stats = collectStats(obj);

    const type = obj.isMesh ? 'Mesh' : obj.isGroup ? 'Group' : obj.type;
    this.el.meta.innerHTML = [
      `世界位置 <b>${fmt(world.x, 2)}, ${fmt(world.y, 2)}, ${fmt(world.z, 2)}</b>`,
      `尺寸 <b>${fmt(size.x, 2)} × ${fmt(size.y, 2)} × ${fmt(size.z, 2)}</b> m`,
      `类型 <b>${type}</b> · 三角面 <b>${compactNumber(stats.triangles)}</b> · 材质 <b>${stats.materials}</b>`,
    ].join('<br>');
  }

  _pathOf(obj) {
    const parts = [];
    let cur = obj;
    while (cur && cur !== this.selection.viewer.modelRoot) {
      parts.unshift(cur.name || '(未命名)');
      cur = cur.parent;
    }
    return parts.join(' / ');
  }
}
