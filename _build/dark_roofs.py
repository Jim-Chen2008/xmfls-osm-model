from pathlib import Path
p=Path(r'xmfls-osm-model\src\app.js'); s=p.read_text(encoding='utf-8')
s=s.replace("    ground: 0xc1b5a2,\n    schoolGround: 0xd9c9b2,\n    insideWall: 0xe6d9c5,\n    insideTop: 0x8c7c64,\n    outsideWall: 0xa5a69e,\n    outsideTop: 0x81847b,", "    ground: 0xbdb19e,\n    schoolGround: 0xd4c5ae,\n    insideWall: 0xe4d7c3,\n    insideTop: 0x6b6153,\n    outsideWall: 0xa0a199,\n    outsideTop: 0x666a61,")
s=s.replace("const boundaryBand = flatRibbon(DATA.school.polygon, 1.0, .034, new THREE.MeshStandardMaterial({ color: 0x596652, roughness: .95, transparent: true, opacity: .42, side: THREE.DoubleSide }));", "const boundaryBand = flatRibbon(DATA.school.polygon, 1.5, .034, new THREE.MeshStandardMaterial({ color: 0x4c5b4d, roughness: .95, transparent: true, opacity: .55, side: THREE.DoubleSide }));")
s=s.replace("grid.material.opacity = .2;", "grid.material.opacity = .28;")
s=s.replace("const home = { target: new THREE.Vector3(70, 3, -4), theta: .69, phi: 1.04, radius: 550 };", "const home = { target: new THREE.Vector3(86, 3, -4), theta: .69, phi: 1.04, radius: 560 };")
# add model-limits note under the height note
old='''    <p class="note">此份 OSM 抽出的建筑只有 <code>building=yes</code>，没有层数或高度标签。全部建筑先按统一体块拉伸；拖动可调整示意高度。</p>'''
new='''    <p class="note">此份 OSM 抽出的建筑只有 <code>building=yes</code>，没有层数或高度标签。全部建筑先按统一体块拉伸；拖动可调整示意高度。</p>
    <p class="note note-quiet">仅呈现 OSM 记录的几何：不补校门、树木、跑道分道线、室内或建筑命名；道路只画 OSM 中心线，不推测路宽。</p>'''
# operate on html separately below
p.write_text(s,encoding='utf-8')
html=Path(r'xmfls-osm-model\src\index.html'); h=html.read_text(encoding='utf-8')
h=h.replace(old,new)
html.write_text(h,encoding='utf-8')
print('patched')
