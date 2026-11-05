  /* ================= object editor ================= */
  let editorMode = false;
  const EDIT = {
    targets: [], selected: null, history: [], hi: -1,
    pickMeshes: [], box: null
  };
  const EDIT_LS = 'xmfls-layout-v1';

  function editLabelName(f) {
    return '#' + f.label + ' · ' + (f.name || '对象');
  }

  for (const f of FEATURES) {
    if (!f.group) continue;
    const g = f.group;
    const isBuilding = f.kind === '建筑';
    const geomX = f.x - g.position.x;
    const geomZ = f.z - g.position.z;
    const baseLabelY = f.labelDef ? f.labelDef.y : f.y;
    const state = {
      x: f.x, z: f.z, y: g.position.y,
      rot: g.rotation.y, h: g.scale.y
    };
    const t = {
      id: f.label, no: f.no, name: f.name, kind: f.kind,
      isBuilding, f, group: g, geomX, geomZ, baseLabelY,
      initial: { ...state }, state
    };
    f.edit = t;
    EDIT.targets.push(t);
    g.traverse(o => {
      if (o.isMesh) {
        o.userData.editTarget = t;
        EDIT.pickMeshes.push(o);
      }
    });
  }
  EDIT.targets.sort((a, b) => Number(a.no) - Number(b.no));

  const editBox = new THREE.BoxHelper(new THREE.Object3D(), 0xa75437);
  editBox.visible = false;
  scene.add(editBox);
  EDIT.box = editBox;

  const editRay = new THREE.Raycaster();
  const editNdc = new THREE.Vector2();

  function pickEditTarget(clientX, clientY) {
    const nd = screenToNdc(clientX, clientY);
    editNdc.set(nd.x, nd.y);
    editRay.setFromCamera(editNdc, camera);
    const hits = editRay.intersectObjects(EDIT.pickMeshes, false);
    for (const h of hits) {
      if (h.object && h.object.userData.editTarget) return h.object.userData.editTarget;
    }
    return null;
  }

  function snapshotState() {
    return EDIT.targets.map(t => ({
      id: t.id,
      x: +t.state.x.toFixed(3), z: +t.state.z.toFixed(3),
      y: +t.state.y.toFixed(3), rot: +t.state.rot.toFixed(5),
      h: +t.state.h.toFixed(3)
    }));
  }

  function applyTarget(t) {
    const s = t.state;
    t.group.position.x = s.x - t.geomX;
    t.group.position.z = s.z - t.geomZ;
    t.group.position.y = s.y;
    t.group.rotation.y = s.rot;
    t.group.scale.y = s.h;
    t.f.x = s.x; t.f.z = s.z;
    if (t.f.labelDef) {
      t.f.labelDef.x = s.x;
      t.f.labelDef.z = s.z;
      if (t.isBuilding) {
        t.f.y = s.y + s.h + 2.5;
        t.f.labelDef.y = t.f.y;
      } else {
        t.f.y = t.baseLabelY + (s.y - t.initial.y);
        t.f.labelDef.y = t.f.y;
      }
    }
    if (Math.abs(s.rot - t.initial.rot) > 1e-6) {
      t.f.angle = ((s.rot * 180 / Math.PI) % 180 + 180) % 180;
    }
    if (EDIT.selected === t) {
      editBox.setFromObject(t.group);
      fillEditFields();
      if (t.isBuilding) {
        $('#selHeight').textContent = s.h.toFixed(1) + ' m（已编辑）';
      }
    }
  }

  function applySnapshot(snap) {
    const byId = new Map(snap.map(s => [s.id, s]));
    for (const t of EDIT.targets) {
      const s = byId.get(t.id);
      if (!s) continue;
      t.state = { ...s };
      applyTarget(t);
    }
    if (EDIT.selected) editBox.setFromObject(EDIT.selected.group);
  }

  function updateHistoryButtons() {
    const u = $('#undoEdit'), r = $('#redoEdit');
    if (u) u.disabled = EDIT.hi <= 0;
    if (r) r.disabled = EDIT.hi >= EDIT.history.length - 1;
  }

  function saveLocal() {
    try {
      localStorage.setItem(EDIT_LS, JSON.stringify({
        format: 'xmfls-layout', version: 1, savedAt: new Date().toISOString(),
        objects: snapshotState()
      }));
    } catch (e) {}
  }

  function commitHistory() {
    const s = snapshotState();
    const cur = EDIT.history[EDIT.hi];
    if (cur && JSON.stringify(cur) === JSON.stringify(s)) {
      updateHistoryButtons(); return;
    }
    EDIT.history = EDIT.history.slice(0, EDIT.hi + 1);
    EDIT.history.push(s);
    EDIT.hi = EDIT.history.length - 1;
    saveLocal();
    updateHistoryButtons();
    setEditStatus('已记录修改');
  }

  function undoEdit() {
    if (EDIT.hi <= 0) return;
    EDIT.hi--;
    applySnapshot(EDIT.history[EDIT.hi]);
    saveLocal();
    updateHistoryButtons();
    setEditStatus('已撤销');
  }
  function redoEdit() {
    if (EDIT.hi >= EDIT.history.length - 1) return;
    EDIT.hi++;
    applySnapshot(EDIT.history[EDIT.hi]);
    saveLocal();
    updateHistoryButtons();
    setEditStatus('已反撤销');
  }

  function fillEditFields() {
    const t = EDIT.selected;
    if (!t) return;
    $('#edX').value = t.state.x.toFixed(2);
    $('#edZ').value = t.state.z.toFixed(2);
    $('#edY').value = t.state.y.toFixed(2);
    $('#edR').value = (((t.state.rot * 180 / Math.PI) % 360 + 360) % 360).toFixed(1);
    $('#edH').value = t.isBuilding ? t.state.h.toFixed(2) : t.state.h.toFixed(3);
    $('#edHLabel').textContent = t.isBuilding ? '高度' : '高度×';
    $('#edHUnit').textContent = t.isBuilding ? 'm' : '×';
    $('#editHeightNote').textContent = t.isBuilding ? '该建筑单独高度（米）；不影响其他建筑。' : '补全构筑物的垂直缩放；椭圆可用 Y 位置整体抬升。';
  }

  function selectEditTarget(t) {
    EDIT.selected = t || null;
    const form = $('#editForm'), empty = $('#editEmpty');
    if (!t) {
      form.hidden = true; empty.hidden = false;
      editBox.visible = false;
      $('#editModeLabel').textContent = '选择对象';
      $('#editName').textContent = '—';
      $('#editStatus').textContent = '';
      return;
    }
    empty.hidden = true; form.hidden = false;
    $('#editModeLabel').textContent = '已选 #' + t.id;
    $('#editName').textContent = editLabelName(t.f);
    fillEditFields();
    editBox.setFromObject(t.group);
    editBox.visible = true;
    if (t.isBuilding && t.f.rec) {
      showBuilding(t.f.rec);
      $('#selHeight').textContent = t.state.h.toFixed(1) + ' m（已编辑）';
    } else {
      dbgSel.textContent = editLabelName(t.f) + ' · X ' + fmtCoord(t.state.x) + ' · Z ' + fmtCoord(t.state.z);
    }
    const panel = $('#panel');
    if (panel && panel.scrollTop > 0) {
      const block = $('#editBlock');
      if (block) block.scrollIntoView({ block: 'nearest' });
    }
  }

  function setEditStatus(msg) {
    const el = $('#editStatus');
    if (el) el.textContent = msg || '';
  }

  function setEditorMode(on) {
    editorMode = !!on;
    const block = $('#editBlock'), btn = $('#editToggle');
    if (block) block.hidden = !editorMode;
    if (btn) {
      btn.classList.toggle('active', editorMode);
      btn.textContent = editorMode ? '退出编辑' : '编辑';
    }
    const slider = $('#heightSlider');
    if (slider) slider.disabled = editorMode;
    if (!editorMode) {
      editBox.visible = false;
      setEditStatus('已退出编辑模式');
    } else {
      selectEditTarget(EDIT.selected || null);
      setEditStatus('编辑模式：点击对象选择；高度滑块已停用');
    }
  }

  function setEditField(key, value, commit) {
    const t = EDIT.selected;
    if (!t || !Number.isFinite(value)) return;
    if (key === 'x' || key === 'z') t.state[key] = value;
    if (key === 'y') t.state.y = value;
    if (key === 'rot') t.state.rot = value * Math.PI / 180;
    if (key === 'h') {
      t.state.h = t.isBuilding ? Math.max(1, Math.min(80, value)) : Math.max(.05, Math.min(20, value));
    }
    applyTarget(t);
    if (commit) commitHistory();
  }

  function nudgeEdit(field, dir) {
    const t = EDIT.selected;
    if (!t) return;
    const step = field === 'x' || field === 'z' || field === 'y' ? .5 : (field === 'rot' ? 1 : (t.isBuilding ? .5 : .05));
    let v;
    if (field === 'rot') v = (((t.state.rot * 180 / Math.PI) % 360 + 360) % 360) + step * dir;
    else v = t.state[field] + step * dir;
    setEditField(field, v, true);
    fillEditFields();
  }

  function exportEdits() {
    const payload = {
      format: 'xmfls-layout', version: 1,
      exportedAt: new Date().toISOString(),
      objects: snapshotState()
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'xmfls-layout-' + new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-') + '.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    setEditStatus('已导出 ' + payload.objects.length + ' 个对象');
  }

  function importEdits(text) {
    let data;
    try { data = JSON.parse(text); } catch (e) { setEditStatus('JSON 解析失败'); return; }
    const list = Array.isArray(data) ? data : data.objects;
    if (!Array.isArray(list)) { setEditStatus('找不到 objects 数组'); return; }
    const byId = new Map(EDIT.targets.map(t => [t.id, t]));
    let n = 0;
    for (const o of list) {
      const t = byId.get(String(o.id));
      if (!t) continue;
      if (Number.isFinite(o.x)) t.state.x = o.x;
      if (Number.isFinite(o.z)) t.state.z = o.z;
      if (Number.isFinite(o.y)) t.state.y = o.y;
      if (Number.isFinite(o.rot)) t.state.rot = o.rot;
      if (Number.isFinite(o.h)) t.state.h = o.h;
      applyTarget(t); n++;
    }
    commitHistory();
    if (EDIT.selected) selectEditTarget(EDIT.selected);
    setEditStatus('已导入 ' + n + ' 个对象');
  }

  // restore local layout if valid
  const initialSnapshot = snapshotState();
  let restored = false;
  try {
    const raw = localStorage.getItem(EDIT_LS);
    if (raw) {
      const data = JSON.parse(raw);
      if (data && Array.isArray(data.objects) && data.objects.length) {
        applySnapshot(data.objects);
        restored = true;
      }
    }
  } catch (e) {}
  EDIT.initialSnapshot = initialSnapshot;
  EDIT.history = [initialSnapshot, snapshotState()];
  EDIT.hi = 1;
  if (!restored) { EDIT.history = [initialSnapshot]; EDIT.hi = 0; }
  updateHistoryButtons();
  if (restored) setEditStatus('已恢复上次编辑；可撤销回到原始');

  // wire editor UI
  $('#editToggle').addEventListener('click', () => setEditorMode(!editorMode));
  $('#closeEdit').addEventListener('click', () => setEditorMode(false));
  $('#undoEdit').addEventListener('click', undoEdit);
  $('#redoEdit').addEventListener('click', redoEdit);
  $('#exportEdit').addEventListener('click', exportEdits);
  $('#importEdit').addEventListener('click', () => $('#importFile').click());
  $('#importFile').addEventListener('change', e => {
    const f = e.target.files && e.target.files[0];
    if (!f) return;
    const reader = new FileReader();
    reader.onload = () => importEdits(reader.result);
    reader.readAsText(f);
    e.target.value = '';
  });
  $('#resetObj').addEventListener('click', () => {
    if (!EDIT.selected) return;
    EDIT.selected.state = { ...EDIT.selected.initial };
    applyTarget(EDIT.selected);
    commitHistory(); fillEditFields();
  });
  $('#resetAll').addEventListener('click', () => {
    for (const t of EDIT.targets) { t.state = { ...t.initial }; applyTarget(t); }
    commitHistory();
    if (EDIT.selected) selectEditTarget(EDIT.selected);
  });
  $$('.nudge').forEach(btn => btn.addEventListener('click', () => nudgeEdit(btn.dataset.field, Number(btn.dataset.dir))));
  const fieldMap = { edX: 'x', edZ: 'z', edY: 'y', edR: 'rot', edH: 'h' };
  for (const [id, key] of Object.entries(fieldMap)) {
    const input = $('#' + id);
    input.addEventListener('input', () => setEditField(key, parseFloat(input.value), false));
    input.addEventListener('change', () => setEditField(key, parseFloat(input.value), true));
  }
  window.addEventListener('keydown', e => {
    if (!editorMode) return;
    if (e.ctrlKey || e.metaKey) {
      if (e.code === 'KeyZ') { e.preventDefault(); if (e.shiftKey) redoEdit(); else undoEdit(); }
      if (e.code === 'KeyY') { e.preventDefault(); redoEdit(); }
    }
  });

  // integrated real-image overlay modal
  $('#overlayBtn').addEventListener('click', () => {
    const modal = $('#overlayModal'), frame = $('#overlayFrame');
    if (frame && !frame.getAttribute('src')) {
      frame.setAttribute('src', window.__CALIB_PAGE || '坐标校准-实景叠图.html');
    }
    modal.hidden = false;
  });
  $('#overlayClose').addEventListener('click', () => { $('#overlayModal').hidden = true; });
  $('#overlayModal').addEventListener('click', e => { if (e.target === $('#overlayModal')) $('#overlayModal').hidden = true; });
  window.addEventListener('keydown', e => { if (e.key === 'Escape') $('#overlayModal').hidden = true; });
