from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("LMAT.plaza = new THREE.MeshStandardMaterial({ color: 0xd9c58f, roughness: .92, metalness: .01 });", "LMAT.plaza = new THREE.MeshStandardMaterial({ color: 0xd2ae58, roughness: .96, metalness: 0 });")
s=s.replace("new THREE.LineBasicMaterial({ color: 0x987d4b, transparent: true, opacity: .52 })", "new THREE.LineBasicMaterial({ color: 0x7b5a24, transparent: true, opacity: .8 })")
p.write_text(s,encoding='utf-8'); print('yellow contrast')
