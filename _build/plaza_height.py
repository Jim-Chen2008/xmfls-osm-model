from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("    disc.rotation.x = -Math.PI / 2; disc.scale.set(plazaRX, plazaRZ, 1);\n    g.add(lmAdd(disc, false, true));", "    disc.rotation.x = -Math.PI / 2; disc.scale.set(plazaRX, plazaRZ, 1); disc.position.y = .036;\n    g.add(lmAdd(disc, false, true));")
s=s.replace("    ring.rotation.x = -Math.PI / 2; ring.scale.set(plazaRX, plazaRZ, 1);\n    g.add(lmAdd(ring, false, true));", "    ring.rotation.x = -Math.PI / 2; ring.scale.set(plazaRX, plazaRZ, 1); ring.position.y = .042;\n    g.add(lmAdd(ring, false, true));")
p.write_text(s,encoding='utf-8'); print('fixed disc height')
