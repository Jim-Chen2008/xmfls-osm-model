from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
# create track group and draw track into it
s=s.replace("  /* ---------- school ground / boundary ---------- */", "  G.track = new THREE.Group();\n  scene.add(G.track);\n\n  /* ---------- school ground / boundary ---------- */")
s=s.replace("    const outer = flatPolygon(DATA.track.outer.polygon, .045, trackOuterMat);\n    if (outer) G.sports.add(outer);", "    const outer = flatPolygon(DATA.track.outer.polygon, .045, trackOuterMat);\n    if (outer) G.track.add(outer);")
s=s.replace("      const inner = flatPolygon(DATA.track.inner.polygon, .058, pitchMat);\n      if (inner) G.sports.add(inner);", "      const inner = flatPolygon(DATA.track.inner.polygon, .058, pitchMat);\n      if (inner) G.track.add(inner);")
s=s.replace("      G.sports.add(lineLoop(DATA.track.inner.polygon, .064, new THREE.LineBasicMaterial", "      G.track.add(lineLoop(DATA.track.inner.polygon, .064, new THREE.LineBasicMaterial")
# remove parent sports shift, set track shift
s=s.replace("  const TRACK_SHIFT_X = -2;\n  G.sports.position.x = TRACK_SHIFT_X;", "  const TRACK_SHIFT_X = -2;\n  G.track.position.x = TRACK_SHIFT_X;")
# attach track feature group
s=s.replace("addFeature({ kind: '场地', name: '田径场', x: outerC[0] + TRACK_SHIFT_X, z: outerC[1] + 23, y: 2.4, angle: CAMPUS_BEARING, layer: G.sports });", "const trackFeat = addFeature({ kind: '场地', name: '田径场', x: outerC[0] + TRACK_SHIFT_X, z: outerC[1] + 23, y: 2.4, angle: CAMPUS_BEARING, layer: G.sports });\n  trackFeat.group = G.track;")
# layer sports includes track
s=s.replace("      if (k === 'sports') G.sports.visible = input.checked;", "      if (k === 'sports') { G.sports.visible = input.checked; G.track.visible = input.checked; }")
p.write_text(s,encoding='utf-8'); print('track group patched')
