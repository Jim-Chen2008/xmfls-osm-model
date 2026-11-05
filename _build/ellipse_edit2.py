from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("    $('#edHLabel').textContent = t.isBuilding ? '高度' : '高度×';\n    $('#edHUnit').textContent = t.isBuilding ? 'm' : '×';", "    $('#edHLabel').textContent = t.isBuilding ? '高度' : '高度×';\n    $('#edHUnit').textContent = t.isBuilding ? 'm' : '×';\n    const ef = $('#ellipseFields');\n    if (ef) ef.hidden = !t.isEllipse;\n    if (t.isEllipse && $('#edA')) {\n      $('#edA').value = t.state.rx.toFixed(1);\n      $('#edB').value = t.state.rz.toFixed(1);\n    }")
s=s.replace("    if (key === 'h') {\n      t.state.h = t.isBuilding ? Math.max(1, Math.min(80, value)) : Math.max(.05, Math.min(20, value));\n    }", "    if (key === 'h') {\n      t.state.h = t.isBuilding ? Math.max(1, Math.min(80, value)) : Math.max(.05, Math.min(20, value));\n    }\n    if (key === 'a' || key === 'b') {\n      if (!t.isEllipse) return;\n      const v = Math.max(4, Math.min(400, value));\n      if (key === 'a') t.state.rx = v; else t.state.rz = v;\n    }")
# nudge step: include a/b 1m
s=s.replace("    const step = field === 'x' || field === 'z' || field === 'y' ? .5 : (field === 'rot' ? 1 : (t.isBuilding ? .5 : .05));", "    const step = field === 'x' || field === 'z' || field === 'y' ? .5 : (field === 'rot' ? 1 : (field === 'a' || field === 'b' ? 1 : (t.isBuilding ? .5 : .05)));")
s=s.replace("    if (field === 'rot') v = (((t.state.rot * 180 / Math.PI) % 360 + 360) % 360) + step * dir;\n    else v = t.state[field] + step * dir;", "    if (field === 'rot') v = (((t.state.rot * 180 / Math.PI) % 360 + 360) % 360) + step * dir;\n    else if (field === 'a' || field === 'b') v = t.state[field === 'a' ? 'rx' : 'rz'] + step * dir;\n    else v = t.state[field] + step * dir;")
# import axes
s=s.replace("      if (Number.isFinite(o.h)) t.state.h = o.h;\n      applyTarget(t); n++;", "      if (Number.isFinite(o.h)) t.state.h = o.h;\n      if (t.isEllipse && Number.isFinite(o.rx)) t.state.rx = o.rx;\n      if (t.isEllipse && Number.isFinite(o.rz)) t.state.rz = o.rz;\n      applyTarget(t); n++;")
# field map
s=s.replace("const fieldMap = { edX: 'x', edZ: 'z', edY: 'y', edR: 'rot', edH: 'h' };", "const fieldMap = { edX: 'x', edZ: 'z', edY: 'y', edR: 'rot', edH: 'h', edA: 'a', edB: 'b' };")
p.write_text(s,encoding='utf-8'); print('ellipse form patched')
