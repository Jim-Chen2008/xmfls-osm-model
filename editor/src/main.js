import * as THREE from 'three';
import { Viewer } from './core/Viewer.js';
import { CameraRig } from './core/CameraRig.js';
import { FirstPerson } from './core/FirstPerson.js';
import { SelectionManager } from './core/SelectionManager.js';
import { History } from './core/History.js';
import { ModelIO } from './core/ModelIO.js';
import { SceneTree } from './ui/SceneTree.js';
import { TransformPanel } from './ui/TransformPanel.js';
import { toast } from './ui/Toast.js';
import { boxSize, collectStats, compactNumber, downloadBlob, fmt, safeFilename } from './utils/helpers.js';

/* ============================================================
   应用装配
   ============================================================ */

const viewportEl = document.getElementById('viewport');
const loaderEl = document.getElementById('loader');
const loaderText = document.getElementById('loader-text');

const viewer = new Viewer(viewportEl);
const rig = new CameraRig({ camera: viewer.camera, domElement: viewer.domElement, viewer });
const history = new History();
const selection = new SelectionManager({ viewer, rig, history });
const io = new ModelIO({ viewer, history });
const firstPerson = new FirstPerson({ camera: viewer.camera, viewer, domElement: viewer.domElement });

const tree = new SceneTree({
  container: document.getElementById('scene-tree'),
  viewer,
  selection,
  rig,
  countEl: document.getElementById('scene-count'),
});

const panel = new TransformPanel({
  container: document.getElementById('transform-rows'),
  selection,
  elements: {
    name: document.getElementById('sel-name'),
    path: document.getElementById('sel-path'),
    badge: document.getElementById('sel-badge'),
    meta: document.getElementById('sel-meta'),
    actions: {
      parent: document.getElementById('btn-select-parent'),
      focus: document.getElementById('btn-focus'),
      exportSelected: document.getElementById('btn-export-selected'),
      group: document.getElementById('btn-group'),
      ungroup: document.getElementById('btn-ungroup'),
    },
  },
});

/* ============================================================
   小工具
   ============================================================ */

function showLoader(text) {
  if (text) loaderText.textContent = text;
  loaderEl.classList.remove('hidden');
}

function hideLoader() {
  loaderEl.classList.add('hidden');
}

function setModeLabel(mode) {
  const chip = document.getElementById('hud-mode-text');
  const map = { edit: '编辑模式', fly: '飞行模式', walk: '第一人称漫游' };
  chip.textContent = map[mode] || '编辑模式';
  document.body.dataset.mode = mode;
  document.getElementById('btn-walk').classList.toggle('on', mode === 'walk');
}

function updateHudSelection(payload) {
  const chip = document.getElementById('hud-selection');
  const stat = document.getElementById('stat-sel');
  const list = payload?.list || [];
  const primary = payload?.primary || null;

  if (!list.length) {
    chip.classList.add('hidden');
    stat.textContent = '未选中';
    return;
  }

  chip.classList.remove('hidden');
  if (list.length > 1) {
    chip.textContent = `多选 ${list.length} 个对象`;
    stat.textContent = `多选 ${list.length} 个 · ${primary?.name || ''}`;
  } else {
    chip.textContent = primary?.name || '(未命名)';
    stat.textContent = primary?.name || '(未命名)';
  }
}

/** 聚焦当前选中（多选时聚焦整体范围） */
function focusSelection() {
  if (!selection.count) return;
  if (selection.isMulti) {
    const box = new THREE.Box3();
    for (const obj of selection.selectedList) box.union(new THREE.Box3().setFromObject(obj));
    rig.focusBox(box);
  } else {
    rig.focusObject(selection.selected);
  }
}

function updateHistoryButtons() {
  const state = history.state();
  const undoBtn = document.getElementById('btn-undo');
  const redoBtn = document.getElementById('btn-redo');
  undoBtn.disabled = !state.canUndo;
  redoBtn.disabled = !state.canRedo;
  undoBtn.title = state.canUndo ? `撤销：${state.undoLabel} (Ctrl+Z)` : '没有可撤销的操作';
  redoBtn.title = state.canRedo ? `重做：${state.redoLabel} (Ctrl+Shift+Z)` : '没有可重做的操作';
}

function updateModelInfo() {
  const stats = collectStats(viewer.modelRoot);
  const size = boxSize(viewer.bounds);
  document.getElementById('info-name').textContent = io.modelFile || io.modelName;
  document.getElementById('info-name').title = io.modelFile || '';
  document.getElementById('info-size').textContent = `${fmt(size.x, 1)} × ${fmt(size.z, 1)} × ${fmt(size.y, 1)} m`;
  document.getElementById('info-counts').textContent = `${stats.meshes} / ${stats.materials}`;
  document.getElementById('info-tris').textContent = compactNumber(stats.triangles);
}

/* ============================================================
   事件接线
   ============================================================ */

selection.on('select', (payload) => {
  panel.setSelection(payload.list, payload.primary);
  tree.setActiveList(payload.list, payload.primary);
  updateHudSelection(payload);
});

// 组合 / 解组后结构变化，重建场景树
selection.on('structure', () => {
  tree.build({ preserveOpen: true });
});

selection.on('change', () => {
  panel.refresh();
});

selection.on('transform-restored', () => {
  panel.refresh();
  tree.refreshVisibility();
});

selection.on('visibility', () => {
  tree.refreshVisibility();
});

history.on('change', updateHistoryButtons);

/* ---------- 模型加载 ---------- */
io.on('loading', (text) => showLoader(text));

io.on('loaded', ({ box, name }) => {
  tree.build();
  panel.setSelection([], null);
  selection.select(null);
  rig.enable();
  rig.fit(box, { animate: false });
  updateModelInfo();
  updateHistoryButtons();
  setModeLabel('edit');
  hideLoader();
  toast(`已载入「${name}」`, 'success');
});

/* ---------- 相机模式 ---------- */
rig.on('mode', (mode) => {
  if (mode === 'fly') {
    selection.setGizmoVisible(false);
    setModeLabel('fly');
  } else if (mode === 'edit') {
    selection.setGizmoVisible(true);
    setModeLabel('edit');
  }
});

function enterWalk() {
  if (firstPerson.active) return;

  // 从“当前视线落点”进入场景：手柄的环绕中心就是玩家落脚点
  const b = viewer.bounds;
  const t = rig.orbit.target;
  const dir = new THREE.Vector3();
  viewer.camera.getWorldDirection(dir);
  const spawn = {
    x: THREE.MathUtils.clamp(t.x, b.min.x + 1, b.max.x - 1),
    z: THREE.MathUtils.clamp(t.z, b.min.z + 1, b.max.z - 1),
    yaw: Math.atan2(-dir.x, -dir.z),
  };

  selection.setGizmoVisible(false);
  rig.disable();
  firstPerson.enter(spawn);
  setModeLabel('walk');
}

function exitWalk() {
  if (!firstPerson.active) return;
  firstPerson.exit();
  document.body.dataset.mode = 'edit';
  setModeLabel('edit');
  rig.enable();
  const dir = new THREE.Vector3();
  viewer.camera.getWorldDirection(dir);
  rig.orbit.target.copy(viewer.camera.position).addScaledVector(dir, 24);
  rig.orbit.update();
  selection.setGizmoVisible(true);
}

firstPerson.on('exit', () => {
  if (document.body.dataset.mode === 'walk') exitWalk();
});

firstPerson.on('lock', (locked) => {
  const tip = document.getElementById('walk-tip');
  tip.textContent = locked ? 'Esc 退出漫游' : '点击画面锁定视角';
});

/* ---------- 第一人称开关 ---------- */
document.getElementById('btn-walk').addEventListener('click', () => {
  if (document.body.dataset.mode === 'walk') exitWalk();
  else enterWalk();
});

/* ---------- 导入 ---------- */
const fileInput = document.getElementById('file-input');

async function importFile(file) {
  if (!file) return;
  showLoader(`正在解析 ${file.name}…`);
  try {
    await io.loadFile(file);
  } catch (err) {
    console.error(err);
    hideLoader();
    toast(`导入失败：${err.message || err}`, 'error', 4200);
  } finally {
    fileInput.value = '';
  }
}

document.getElementById('btn-import').addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => importFile(fileInput.files?.[0]));

/* ---------- 拖拽导入 ---------- */
const dropzone = document.getElementById('dropzone');
let dragDepth = 0;

viewportEl.addEventListener('dragenter', (e) => {
  e.preventDefault();
  dragDepth += 1;
  dropzone.classList.add('active');
});
viewportEl.addEventListener('dragover', (e) => e.preventDefault());
viewportEl.addEventListener('dragleave', (e) => {
  e.preventDefault();
  dragDepth = Math.max(0, dragDepth - 1);
  if (!dragDepth) dropzone.classList.remove('active');
});
viewportEl.addEventListener('drop', (e) => {
  e.preventDefault();
  dragDepth = 0;
  dropzone.classList.remove('active');
  const file = e.dataTransfer?.files?.[0];
  if (file) importFile(file);
});

/* ---------- 导出 ---------- */
document.getElementById('btn-export').addEventListener('click', async () => {
  const btn = document.getElementById('btn-export');
  btn.disabled = true;
  try {
    const { filename } = await io.exportScene();
    toast(`已导出 ${filename}`, 'success', 3400);
  } catch (err) {
    console.error(err);
    toast(`导出失败：${err.message || err}`, 'error', 4000);
  } finally {
    btn.disabled = false;
  }
});

document.getElementById('btn-export-selected').addEventListener('click', async () => {
  if (!selection.selected) return;
  if (selection.isMulti) {
    toast('多选状态请先「组合」成一个整体再导出', 'error', 2600);
    return;
  }
  try {
    const { filename } = await io.exportObject(selection.selected);
    toast(`已导出选中对象：${filename}`, 'success', 3400);
  } catch (err) {
    toast(`导出失败：${err.message || err}`, 'error', 4000);
  }
});

/* ---------- 撤销 / 重做 ---------- */
document.getElementById('btn-undo').addEventListener('click', () => {
  const cmd = history.undo();
  if (cmd) toast(`撤销：${cmd.label}`, 'info', 1500);
});
document.getElementById('btn-redo').addEventListener('click', () => {
  const cmd = history.redo();
  if (cmd) toast(`重做：${cmd.label}`, 'info', 1500);
});

/* ---------- 变换模式 ---------- */
const modeGroup = document.getElementById('gizmo-mode');
modeGroup.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-mode]');
  if (!btn) return;
  setGizmoMode(btn.dataset.mode);
});

function setGizmoMode(mode) {
  selection.setGizmoMode(mode);
  for (const b of modeGroup.querySelectorAll('button')) {
    b.classList.toggle('on', b.dataset.mode === mode);
  }
}

const spaceGroup = document.getElementById('gizmo-space');
spaceGroup.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-space]');
  if (!btn) return;
  selection.setGizmoSpace(btn.dataset.space);
  for (const b of spaceGroup.querySelectorAll('button')) {
    b.classList.toggle('on', b.dataset.space === btn.dataset.space);
  }
});

/* ---------- 场景树搜索 ---------- */
document.getElementById('tree-search').addEventListener('input', (e) => {
  tree.filter(e.target.value);
});

/* ---------- 视图开关 ---------- */
document.getElementById('chk-grid').addEventListener('change', (e) => {
  viewer.setGridVisible(e.target.checked);
});

document.getElementById('chk-shadow').addEventListener('change', (e) => {
  viewer.setShadowEnabled(e.target.checked);
});

document.getElementById('chk-wireframe').addEventListener('change', (e) => {
  const on = e.target.checked;
  viewer.modelRoot.traverse((obj) => {
    if (!obj.isMesh) return;
    const mats = Array.isArray(obj.material) ? obj.material : [obj.material];
    for (const m of mats) {
      if (!m) continue;
      m.wireframe = on;
      m.needsUpdate = true;
    }
  });
});

document.getElementById('chk-snap').addEventListener('change', (e) => {
  selection.setSnapEnabled(e.target.checked);
});

/* ---------- 视角 / 截图 ---------- */
document.getElementById('btn-reset-view').addEventListener('click', () => {
  rig.fit(viewer.bounds, { animate: true });
});

document.getElementById('btn-focus').addEventListener('click', () => {
  focusSelection();
});

document.getElementById('btn-group').addEventListener('click', () => {
  const group = selection.groupSelected();
  if (group) toast(`已组合为「${group.name}」，可整体移动 / 旋转 / 缩放`, 'success', 2600);
});

document.getElementById('btn-ungroup').addEventListener('click', () => {
  const members = selection.ungroupSelected();
  if (members) toast(`已解组，拆出 ${members.length} 个对象`, 'info', 2200);
});

document.getElementById('btn-select-parent').addEventListener('click', () => {
  selection.selectParent();
});

document.getElementById('btn-fly').addEventListener('click', () => {
  if (rig.mode === 'fly') rig.exitFly();
  else {
    rig.enterFly();
    // 指针锁定失败（例如浏览器限制）时自动回退，避免卡在飞行模式
    setTimeout(() => {
      if (rig.mode === 'fly' && !rig.pointerLocked) {
        rig.exitFly();
        toast('浏览器未授予指针锁定，可继续用鼠标拖拽旋转视角', 'error', 3200);
      }
    }, 700);
  }
});

document.getElementById('btn-save-shot').addEventListener('click', () => {
  viewer.renderer.render(viewer.scene, viewer.camera);
  viewer.domElement.toBlob((blob) => {
    if (!blob) return;
    const name = `${safeFilename(io.modelName, 'scene')}-${Date.now()}.png`;
    downloadBlob(blob, name);
    toast('截图已保存', 'success', 1800);
  }, 'image/png');
});

/* ---------- 操作说明折叠 ---------- */
const hints = document.getElementById('hints');
document.getElementById('hints-toggle').addEventListener('click', () => {
  const collapsed = hints.classList.toggle('collapsed');
  document.getElementById('hints-toggle').setAttribute('aria-expanded', String(!collapsed));
});
if (window.innerWidth < 1200) hints.classList.add('collapsed');

/* ============================================================
   键盘快捷键
   ============================================================ */

function isTyping() {
  const el = document.activeElement;
  if (!el) return false;
  return el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable;
}

window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (document.body.dataset.mode === 'walk') exitWalk();
    else if (rig.mode === 'fly') rig.exitFly();
    return;
  }
  if (isTyping()) return;
  if (document.body.dataset.mode === 'walk') return;

  const mod = e.ctrlKey || e.metaKey;

  if (mod && e.key.toLowerCase() === 'z') {
    e.preventDefault();
    if (e.shiftKey) {
      const cmd = history.redo();
      if (cmd) toast(`重做：${cmd.label}`, 'info', 1400);
    } else {
      const cmd = history.undo();
      if (cmd) toast(`撤销：${cmd.label}`, 'info', 1400);
    }
    return;
  }

  if (mod && e.key.toLowerCase() === 'g') {
    e.preventDefault();
    if (e.shiftKey) {
      const members = selection.ungroupSelected();
      if (members) toast(`已解组，拆出 ${members.length} 个对象`, 'info', 2200);
    } else {
      const group = selection.groupSelected();
      if (group) toast(`已组合为「${group.name}」`, 'success', 2400);
      else toast('请先按住 Ctrl 多选至少 2 个对象', 'info', 2200);
    }
    return;
  }

  if (mod && e.key.toLowerCase() === 'y') {
    e.preventDefault();
    const cmd = history.redo();
    if (cmd) toast(`重做：${cmd.label}`, 'info', 1400);
    return;
  }

  if (mod) return;

  switch (e.key) {
    case '1':
      setGizmoMode('translate');
      break;
    case '2':
      setGizmoMode('rotate');
      break;
    case '3':
      setGizmoMode('scale');
      break;
    case 'f':
    case 'F':
      focusSelection();
      break;
    case 'v':
    case 'V':
      enterWalk();
      break;
    case 'b':
    case 'B':
      if (rig.mode === 'fly') rig.exitFly();
      else rig.enterFly();
      break;
    case 'Delete':
    case 'Backspace':
      if (selection.count) {
        e.preventDefault();
        const n = selection.count;
        selection.hideSelected();
        toast(n > 1 ? `已隐藏 ${n} 个对象（Ctrl+Z 可恢复）` : '已隐藏选中对象（Ctrl+Z 可恢复）', 'info', 2200);
      }
      break;
    default:
      break;
  }
});

/* ============================================================
   运行
   ============================================================ */

let fpsFrames = 0;
let fpsTime = 0;
let statTimer = 0;

viewer.start((dt) => {
  rig.update(dt);
  firstPerson.update(dt);
  selection.update();

  // FPS 与统计
  fpsFrames += 1;
  fpsTime += dt;
  statTimer += dt;
  if (statTimer > 0.5) {
    const fps = fpsFrames / Math.max(fpsTime, 1e-4);
    document.getElementById('stat-fps').textContent = `${fps.toFixed(0)} FPS`;
    const tris = viewer.renderer.info.render.triangles;
    document.getElementById('stat-tris').textContent = `${compactNumber(tris)} 三角面`;
    const p = viewer.camera.position;
    document.getElementById('stat-coord').textContent = `相机 ${fmt(p.x, 1)}, ${fmt(p.y, 1)}, ${fmt(p.z, 1)}`;
    fpsFrames = 0;
    fpsTime = 0;
    statTimer = 0;
  }
});

updateHistoryButtons();
setModeLabel('edit');
panel.setSelection([], null);
showLoader('正在载入默认校园模型…');

io.loadDefault().catch((err) => {
  console.error(err);
  hideLoader();
  toast(`默认模型加载失败：${err.message || err}`, 'error', 5000);
});

// 便于在控制台调试
window.__editor = { viewer, rig, selection, history, io, tree, panel, firstPerson };
