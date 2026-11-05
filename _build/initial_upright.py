from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
old="""  try {
    renderer.render(scene, camera);"""
new="""  // open in the straightened editor view; the 3D overview remains one click away
  setView('upright');

  try {
    renderer.render(scene, camera);"""
if old not in s: raise SystemExit('bottom anchor missing')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8'); print('initial upright')
