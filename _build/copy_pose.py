from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
anchor="$('#clearSelection').addEventListener('click', () => showBuilding(null));"
code=r'''  /* ---------- copy pose (always available) ---------- */
  let toastTimer = 0;
  function showToast(msg) {
    const t = $('#toast');
    if (!t) return;
    t.textContent = msg;
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), 1800);
  }
  function poseText() {
    const heading = (((-fly.yaw * 180 / Math.PI) % 360) + 360) % 360;
    const pitch = fly.pitch * 180 / Math.PI;
    return 'X ' + camera.position.x.toFixed(2) + ', Z ' + camera.position.z.toFixed(2) +
      ', Y ' + camera.position.y.toFixed(2) + ', HDG ' + heading.toFixed(2) + '°, PITCH ' + pitch.toFixed(2) + '°' +
      (WALK.active ? ' [第一人称]' : ' [飞行]');
  }
  function copyPose() {
    const txt = poseText();
    const done = () => showToast('已复制：' + txt);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(txt).then(done).catch(() => { window.prompt('复制坐标 / 角度', txt); });
    } else {
      window.prompt('复制坐标 / 角度', txt);
    }
  }
  $('#copyPose').addEventListener('click', copyPose);
  window.addEventListener('keydown', e => {
    if (e.code !== 'KeyC' || e.ctrlKey || e.metaKey || e.altKey) return;
    const a = document.activeElement;
    if (a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' || a.isContentEditable)) return;
    e.preventDefault();
    copyPose();
  });

'''
if anchor not in s: raise SystemExit('clear selection anchor missing')
s=s.replace(anchor, code+anchor,1)
s=s.replace("window.__MODEL = { scene, camera, renderer, view, fly, buildingViews, showBuilding, G, sun, FEATURES, focusFeature, EDIT, setEditorMode, selectEditTarget, exportEdits, importEdits, height: () => height };",
            "window.__MODEL = { scene, camera, renderer, view, fly, buildingViews, showBuilding, G, sun, FEATURES, focusFeature, EDIT, setEditorMode, selectEditTarget, exportEdits, importEdits, enterWalk, leaveWalk, copyPose, height: () => height };")
p.write_text(s,encoding='utf-8'); print('copy pose added')
