from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("    const isBuilding = f.kind === '建筑';\n    const geomX", "    const isBuilding = f.kind === '建筑';\n    const isEllipse = f.kind === '广场' || f.label === '32';\n    const geomX")
s=s.replace("    const state = {\n      x: f.x, z: f.z, y: g.position.y,\n      rot: g.rotation.y, h: g.scale.y\n    };", "    const state = {\n      x: f.x, z: f.z, y: g.position.y,\n      rot: g.rotation.y, h: g.scale.y\n    };\n    if (isEllipse) { state.rx = 57.6418 * 2; state.rz = 18.5498 * 2; }")
s=s.replace("      isBuilding, f, group: g, geomX, geomZ, baseLabelY,", "      isBuilding, isEllipse, f, group: g, geomX, geomZ, baseLabelY,")
s=s.replace("      h: +t.state.h.toFixed(3)\n    }));", "      h: +t.state.h.toFixed(3),\n      rx: t.isEllipse ? +t.state.rx.toFixed(3) : undefined,\n      rz: t.isEllipse ? +t.state.rz.toFixed(3) : undefined\n    }));")
s=s.replace("    t.group.scale.y = s.h;\n    t.f.x = s.x;", "    t.group.scale.y = s.h;\n    if (t.isEllipse) {\n      t.group.scale.x = (s.rx / 2) / 57.6418;\n      t.group.scale.z = (s.rz / 2) / 18.5498;\n    }\n    t.f.x = s.x;")
# applySnapshot merge not replace, to preserve rx/rz when old imports
s=s.replace("      t.state = { ...s };\n      applyTarget(t);", "      t.state = { ...t.state, ...s };\n      applyTarget(t);")
p.write_text(s,encoding='utf-8'); print('ellipse state patched')
