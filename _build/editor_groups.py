from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
# building feature groups after feature loop
anchor="  const knownBuildingNames = { '638485974': '体育馆' };"
# insert after the building feature loop; find the addFeature closing in loop
# use specific end block
needle="""      layer: b.inside ? G.inside : G.outside
    });
  }
"""
repl=needle+"""  for (const v of buildingViews) {
    const f = FEATURE_BY_REC.get(v.rec);
    if (f) f.group = v.group;
  }
"""
if needle not in s: raise SystemExit('building feature loop end missing')
s=s.replace(needle,repl,1)
# special addFeature assignments
s=s.replace("    addFeature({ kind: '球场', name: '篮球场 ×4 / 排球场 ×3', x: bcx, z: bcz, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });",
            "    const feat = addFeature({ kind: '球场', name: '篮球场 ×4 / 排球场 ×3', x: bcx, z: bcz, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });\n    feat.group = g;")
s=s.replace("    addFeature({ kind: '球场', name: tf.name, x: tf.x, z: tf.z, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });",
            "    const feat = addFeature({ kind: '球场', name: tf.name, x: tf.x, z: tf.z, y: 3.5, angle: CAMPUS_BEARING, layer: G.landmarks });\n    feat.group = g;")
s=s.replace("    addFeature({ kind: '看台', name: '主席台（南看台）', x: gx, z: gz, y: 7, angle: 79.7, layer: G.landmarks });",
            "    const feat = addFeature({ kind: '看台', name: '主席台（南看台）', x: gx, z: gz, y: 7, angle: 79.7, layer: G.landmarks });\n    feat.group = g;")
s=s.replace("    addFeature({ kind: '平台', name: '台下平台 · 膜结构', x: px, z: pz, y: 8, angle: CAMPUS_BEARING, layer: G.landmarks });",
            "    const feat = addFeature({ kind: '平台', name: '台下平台 · 膜结构', x: px, z: pz, y: 8, angle: CAMPUS_BEARING, layer: G.landmarks });\n    feat.group = g;")
s=s.replace("    addFeature({ kind: '大门', name: '大门', x: gateX, z: gateZ, y: 12, angle: Math.round(gateBearing * 10) / 10, layer: G.landmarks });",
            "    const feat = addFeature({ kind: '大门', name: '大门', x: gateX, z: gateZ, y: 12, angle: Math.round(gateBearing * 10) / 10, layer: G.landmarks });\n    feat.group = g;")
s=s.replace("    addFeature({ kind: '喷泉', name: '喷泉', x: fx, z: fz, y: 4, angle: 0, layer: G.landmarks });",
            "    const feat = addFeature({ kind: '喷泉', name: '喷泉', x: fx, z: fz, y: 4, angle: 0, layer: G.landmarks });\n    feat.group = g;")
# plaza group variable
s=s.replace("  const plazaX = 99.13, plazaZ = -80.445, plazaRX = 57.6418, plazaRZ = 18.5498;",
            "  let plazaGroup = null;\n  const plazaX = 99.13, plazaZ = -80.445, plazaRX = 57.6418, plazaRZ = 18.5498;")
s=s.replace("    const g = new THREE.Group(); g.position.set(plazaX, 0, plazaZ); g.rotation.y = PLAZA_ROT; G.landmarks.add(g);",
            "    const g = new THREE.Group(); g.position.set(plazaX, 0, plazaZ); g.rotation.y = PLAZA_ROT; G.landmarks.add(g); plazaGroup = g;")
s=s.replace("  addFeature({ kind: '广场', name: '黄色网格椭圆广场', x: 99.13, z: -80.445, y: 2, angle: 50.97, layer: G.landmarks });",
            "  const plazaFeat = addFeature({ kind: '广场', name: '黄色网格椭圆广场', x: 99.13, z: -80.445, y: 2, angle: 50.97, layer: G.landmarks });\n  plazaFeat.group = plazaGroup;")
p.write_text(s,encoding='utf-8'); print('groups attached')
