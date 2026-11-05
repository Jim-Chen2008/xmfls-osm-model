from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("LMAT.plaza = new THREE.MeshStandardMaterial({ map: makeYellowGridTexture(), roughness: .92, metalness: .01 });",
            "LMAT.plaza = new THREE.MeshStandardMaterial({ color: 0xd9c58f, roughness: .92, metalness: .01 });")
old="""    const ring = new THREE.Mesh(new THREE.RingGeometry(.97, 1, 96), LMAT.concreteDark);
    ring.rotation.x = -Math.PI / 2; ring.scale.set(plazaRX, plazaRZ, 1);
    g.add(lmAdd(ring, false, true));
  })();"""
new="""    const ring = new THREE.Mesh(new THREE.RingGeometry(.97, 1, 96), LMAT.concreteDark);
    ring.rotation.x = -Math.PI / 2; ring.scale.set(plazaRX, plazaRZ, 1);
    g.add(lmAdd(ring, false, true));
    // grid inside the ellipse; drawn as line segments so it is clipped to the ellipse
    const gp = [];
    for (let lx = -plazaRX + 4; lx < plazaRX; lx += 4) {
      const hz = plazaRZ * Math.sqrt(Math.max(0, 1 - (lx / plazaRX) ** 2));
      gp.push(lx, .046, -hz, lx, .046, hz);
    }
    for (let lz = -plazaRZ + 4; lz < plazaRZ; lz += 4) {
      const hx = plazaRX * Math.sqrt(Math.max(0, 1 - (lz / plazaRZ) ** 2));
      gp.push(-hx, .046, lz, hx, .046, lz);
    }
    const gg = new THREE.BufferGeometry();
    gg.setAttribute('position', new THREE.Float32BufferAttribute(gp, 3));
    g.add(new THREE.LineSegments(gg, new THREE.LineBasicMaterial({ color: 0x987d4b, transparent: true, opacity: .52 })));
  })();"""
if old not in s: raise SystemExit('plaza ring block missing')
s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
cal=Path(r'xmfls-osm-model\src\calibrate.html'); c=cal.read_text(encoding='utf-8')
c=c.replace("{no:'24', name:'篮球场', x:-46, z:-47.5}", "{no:'24', name:'篮/排球', x:-46, z:-47.5}")
c=c.replace("{no:'32', name:'黄网格广场', x:130.5, z:-80.03}", "{no:'32', name:'黄网格椭圆广场', x:121.365, z:-86.935}")
cal.write_text(c,encoding='utf-8')
print('yellow grid + calibration key patched')
