from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
anchor="  G.ground.add(lineLoop(DATA.school.polygon, .036, schoolLineMat));"
addition=anchor+"\n  const dashedBoundaryMat = new THREE.LineDashedMaterial({ color: 0x4e7058, transparent: true, opacity: .55, dashSize: 5, gapSize: 4 });\n  const dashedBoundary = lineLoop(DATA.school.polygon, .046, dashedBoundaryMat);\n  dashedBoundary.computeLineDistances();\n  G.ground.add(dashedBoundary);"
if anchor not in s: raise SystemExit('school line anchor missing')
s=s.replace(anchor, addition)
p.write_text(s,encoding='utf-8')
print('dashed boundary added')
