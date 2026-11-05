from pathlib import Path
p=Path(r'xmfls-osm-model\src\index.html'); s=p.read_text(encoding='utf-8')
s=s.replace('<button class="view-btn" data-view="top">俯视</button>', '<button class="view-btn" data-view="top">俯视</button>\n    <button class="view-btn" data-view="upright">摆正</button>')
p.write_text(s,encoding='utf-8')
q=Path(r'xmfls-osm-model\src\app.js'); a=q.read_text(encoding='utf-8')
# upright branch at top of setView after walk check
old="""  function setView(name) {
    if (name === 'walk') { if (WALK.active) leaveWalk(true); else enterWalk(); return; }
    if (WALK.active) leaveWalk(false);
    let target, theta, phi, radius;"""
new="""  function setView(name) {
    if (name === 'walk') { if (WALK.active) leaveWalk(true); else enterWalk(); return; }
    if (WALK.active) leaveWalk(false);
    if (name === 'upright') {
      setCameraTo(new THREE.Vector3(0, 0, 0), 0, .055, phoneLayout() ? 910 : 610);
      fly.yaw += 10.3 * Math.PI / 180;
      camera.rotation.set(fly.pitch, fly.yaw, 0, 'YXZ');
      view.auto = false;
      const a = $('#autoBtn'); if (a) a.classList.remove('active');
      $$('.view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === 'upright'));
      return;
    }
    let target, theta, phi, radius;"""
if old not in a: raise SystemExit('setView anchor')
a=a.replace(old,new)
# set edit mode to upright
old2="""    } else {
      selectEditTarget(EDIT.selected || null);
      setEditStatus('编辑模式：点击对象选择；高度滑块已停用');
    }"""
new2="""    } else {
      if (!WALK.active) setView('upright');
      selectEditTarget(EDIT.selected || null);
      setEditStatus('编辑模式：点击对象选择；高度滑块已停用');
    }"""
if old2 not in a: raise SystemExit('setEditorMode anchor')
a=a.replace(old2,new2)
q.write_text(a,encoding='utf-8'); print('upright view added')
