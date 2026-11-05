import { isEffectivelyVisible } from '../utils/helpers.js';

const SVG = {
  chevron: '<svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m9 6 6 6-6 6"/></svg>',
  eye: '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M2.6 12S6 5.8 12 5.8 21.4 12 21.4 12 18 18.2 12 18.2 2.6 12 2.6 12Z"/><circle cx="12" cy="12" r="2.8"/></svg>',
  eyeOff: '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4.5 20 20.5"/><path d="M9.7 6.3A9.6 9.6 0 0 1 12 6c6 0 9.4 6 9.4 6a17 17 0 0 1-3 3.6"/><path d="M6.4 7.9A17 17 0 0 0 2.6 12s3.4 6 9.4 6a9 9 0 0 0 3.6-.7"/></svg>',
  group: '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M12 3.2 20.4 7.6v8.8L12 20.8 3.6 16.4V7.6z"/><path d="M12 12 20.4 7.6M12 12 3.6 7.6M12 12v8.8"/></svg>',
  mesh: '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"><path d="M12 3.6 20 8v8l-8 4.4L4 16V8z"/><path d="M4 8l8 4.4L20 8M12 12.4v8"/></svg>',
};

/**
 * 场景结构树：层级展示、单选 / 多选（Ctrl 追加、Shift 连选）、显隐、搜索。
 */
export class SceneTree {
  constructor({ container, viewer, selection, rig, countEl }) {
    this.container = container;
    this.viewer = viewer;
    this.selection = selection;
    this.rig = rig;
    this.countEl = countEl;
    this.rows = new Map();
    this.roots = [];
    this.filtering = false;
    this.anchor = null;
    this._openSet = new Set();
    this.emptyEl = document.createElement('div');
    this.emptyEl.className = 'tree-empty';
    this.emptyEl.textContent = '没有匹配的对象';
    this.emptyEl.style.display = 'none';
  }

  build({ preserveOpen = false } = {}) {
    // 记录展开状态，重建后尽量还原（组合 / 解组后不会“啪”地全收起）
    if (preserveOpen) {
      for (const [uuid, node] of this.rows) {
        if (node.open) this._openSet.add(uuid);
      }
    } else {
      this._openSet.clear();
    }

    this.container.innerHTML = '';
    this.rows.clear();
    this.roots = [];
    this.container.appendChild(this.emptyEl);

    for (const child of this.viewer.modelRoot.children) {
      const node = this._createNode(child, 0);
      this.roots.push(node);
      this.container.appendChild(node.el);
      this.container.appendChild(node.childrenEl);
    }

    let meshes = 0;
    this.viewer.modelRoot.traverse((o) => {
      if (o.isMesh) meshes += 1;
    });
    if (this.countEl) this.countEl.textContent = `${meshes} 网格`;

    if (preserveOpen) this._restoreOpen(this.roots);
    this._applyExpand(this.roots);

    if (this.selection.selectedList.length) {
      this.setActiveList(this.selection.selectedList, this.selection.selected, { scroll: false });
    }
  }

  _restoreOpen(nodes) {
    for (const node of nodes) {
      if (this._openSet.has(node.obj.uuid)) node.open = true;
      if (node.children.length) this._restoreOpen(node.children);
    }
  }

  _createNode(obj, depth) {
    const children = obj.children || [];
    const isGroup = children.length > 0;

    const el = document.createElement('div');
    el.className = 'tree-item';
    el.dataset.type = isGroup ? 'group' : 'mesh';
    el.dataset.uuid = obj.uuid;
    el.style.paddingLeft = `${4 + depth * 13}px`;
    el.title = obj.name;

    const twist = document.createElement('span');
    twist.className = `tree-twist${isGroup ? '' : ' leaf'}`;
    twist.innerHTML = SVG.chevron;

    const icon = document.createElement('span');
    icon.className = 'tree-icon';
    icon.innerHTML = isGroup ? SVG.group : SVG.mesh;

    const label = document.createElement('span');
    label.className = 'tree-label';
    label.textContent = obj.name;

    el.append(twist, icon, label);

    if (isGroup) {
      let meshCount = 0;
      obj.traverse((o) => {
        if (o.isMesh) meshCount += 1;
      });
      const countBadge = document.createElement('span');
      countBadge.className = 'tree-count';
      countBadge.textContent = String(meshCount);
      el.appendChild(countBadge);
    }

    const eye = document.createElement('button');
    eye.className = 'tree-eye';
    eye.type = 'button';
    eye.title = '显示 / 隐藏';
    eye.innerHTML = obj.visible ? SVG.eye : SVG.eyeOff;
    el.appendChild(eye);

    const childrenEl = document.createElement('div');
    childrenEl.className = 'tree-children';
    childrenEl.style.display = 'none';

    const node = {
      obj,
      el,
      twist,
      eye,
      label,
      childrenEl,
      children: [],
      depth,
      // 默认展开模型根节点与较小的图层，超大图层（如几十栋建筑）先折叠
      open: isGroup && (depth === 0 || (depth === 1 && children.length <= 12)),
    };

    this.rows.set(obj.uuid, node);

    el.addEventListener('click', (e) => {
      if (e.target.closest('.tree-eye') || e.target.closest('.tree-twist')) return;

      if (e.shiftKey) {
        const order = this._visibleObjects();
        const from = order.indexOf(this.anchor || obj);
        const to = order.indexOf(obj);
        if (from >= 0 && to >= 0) {
          const [a, b] = from < to ? [from, to] : [to, from];
          this.selection.setSelection(order.slice(a, b + 1), obj);
        } else {
          this.selection.select(obj);
        }
        this.anchor = obj;
        return;
      }

      if (e.ctrlKey || e.metaKey) {
        this.selection.toggle(obj);
        this.anchor = obj;
        return;
      }

      this.selection.select(obj);
      this.anchor = obj;
    });

    el.addEventListener('dblclick', () => {
      this.rig.focusBox(this.viewer.bounds.clone().setFromObject(obj));
    });

    twist.addEventListener('click', (e) => {
      e.stopPropagation();
      if (!isGroup) return;
      node.open = !node.open;
      this._applyExpand([node]);
    });

    eye.addEventListener('click', (e) => {
      e.stopPropagation();
      obj.visible = !obj.visible;
      this._updateEye(obj);
      this.selection.emit('visibility', obj);
    });

    if (isGroup) {
      for (const c of children) {
        const childNode = this._createNode(c, depth + 1);
        node.children.push(childNode);
        childrenEl.appendChild(childNode.el);
        childrenEl.appendChild(childNode.childrenEl);
      }
    }

    return node;
  }

  _visibleObjects() {
    const list = [];
    for (const el of this.container.querySelectorAll('.tree-item')) {
      if (el.style.display === 'none' || el.offsetParent === null) continue;
      const node = this.rows.get(el.dataset.uuid);
      if (node) list.push(node.obj);
    }
    return list;
  }

  _applyExpand(nodes) {
    const walk = (node) => {
      if (node.children.length) {
        node.childrenEl.style.display = node.open ? '' : 'none';
        node.twist.classList.toggle('open', node.open);
      }
      for (const c of node.children) walk(c);
    };
    nodes.forEach(walk);
  }

  _updateEye(obj) {
    const node = this.rows.get(obj.uuid);
    if (!node) return;
    node.eye.innerHTML = obj.visible ? SVG.eye : SVG.eyeOff;
    node.el.classList.toggle('is-hidden', !isEffectivelyVisible(obj));
  }

  refreshVisibility(root = this.viewer.modelRoot) {
    root.traverse((o) => this._updateEye(o));
  }

  setActiveList(list, primary, { scroll = true } = {}) {
    const active = new Set((list || []).map((o) => o.uuid));
    for (const [uuid, node] of this.rows) {
      node.el.classList.toggle('active', active.has(uuid));
      node.el.classList.toggle('primary', !!primary && uuid === primary.uuid);
    }
    if (!list || !list.length) return;

    // 展开所有选中项的祖先链
    for (const obj of list) {
      let parent = obj.parent;
      while (parent && parent !== this.viewer.modelRoot) {
        const parentNode = this.rows.get(parent.uuid);
        if (parentNode && parentNode.children.length) parentNode.open = true;
        parent = parent.parent;
      }
    }
    if (!this.filtering) this._applyExpand(this.roots);

    if (scroll && primary) {
      const node = this.rows.get(primary.uuid);
      if (node) {
        requestAnimationFrame(() => {
          try {
            node.el.scrollIntoView({ block: 'nearest' });
          } catch {
            /* ignore */
          }
        });
      }
    }
  }

  filter(keyword) {
    const q = String(keyword || '').trim().toLowerCase();
    if (!q) {
      this.filtering = false;
      this.emptyEl.style.display = 'none';
      for (const node of this.rows.values()) node.el.style.display = '';
      this._applyExpand(this.roots);
      return;
    }

    this.filtering = true;
    let matches = 0;

    const visit = (node) => {
      const selfMatch = String(node.obj.name || '').toLowerCase().includes(q);
      let childMatch = false;
      for (const child of node.children) {
        if (visit(child)) childMatch = true;
      }
      const show = selfMatch || childMatch;
      node.el.style.display = show ? '' : 'none';
      if (node.children.length) {
        node.childrenEl.style.display = show ? '' : 'none';
        node.twist.classList.toggle('open', show);
      }
      if (selfMatch) matches += 1;
      return show;
    };

    this.roots.forEach(visit);
    this.emptyEl.style.display = matches ? '' : 'none';
  }
}
