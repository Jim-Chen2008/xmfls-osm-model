from pathlib import Path
html = Path(r'xmfls-osm-model\src\index.html')
h = html.read_text(encoding='utf-8')

h = h.replace('<span class="osmbadge">OSM<span>ONLY</span></span>', '<span class="osmbadge">OSM<span>+ 实景</span></span>')
h = h.replace('<p class="sub">仅按 OSM 校界与建筑轮廓构建 · 未使用照片或其他模型参考</p>',
              '<p class="sub">OSM 校界与建筑为底 · 按实景补全看台、网球场、大门与喷泉</p>')
h = h.replace('<div><b>1</b><span>运动场</span></div>', '<div><b>31</b><span>编号对象</span></div>')

# replace the old strict-OSM note
h = h.replace(
    '<p class="note note-quiet">仅呈现 OSM 记录的几何：不补校门、树木、跑道分道线、室内或建筑命名；道路只画 OSM 中心线，不推测路宽。</p>',
    '<p class="note note-quiet">OSM 提供校界、建筑、田径场与道路；看台、平台、网球场、大门、喷泉按实景补全。编号索引含坐标与角度，便于定位调试。</p>'
)

# add layers for real-scene landmarks, codes and guide
old_layer = '''      <label><input type="checkbox" data-layer="context" checked><span>其他学校 / 围墙</span><i class="sw sw-context"></i></label>
      <label><input type="checkbox" data-layer="labels" checked><span>OSM 标注</span><i class="sw sw-label"></i></label>
      <label><input type="checkbox" data-layer="grid" checked><span>50 m 网格</span><i class="sw sw-grid"></i></label>'''
new_layer = '''      <label><input type="checkbox" data-layer="context" checked><span>其他学校 / 围墙</span><i class="sw sw-context"></i></label>
      <label><input type="checkbox" data-layer="landmarks" checked><span>实景补全</span><i class="sw sw-extra"></i></label>
      <label><input type="checkbox" data-layer="guide" checked><span>大门轴线</span><i class="sw sw-guide"></i></label>
      <label><input type="checkbox" data-layer="labels" checked><span>名称标注</span><i class="sw sw-label"></i></label>
      <label><input type="checkbox" data-layer="codes" checked><span>编号</span><i class="sw sw-num"></i></label>
      <label><input type="checkbox" data-layer="grid" checked><span>50 m 网格</span><i class="sw sw-grid"></i></label>'''
if old_layer not in h: raise SystemExit('layer block not found')
h = h.replace(old_layer, new_layer)

# add index block before panel-foot
panel_foot = '  <div class="panel-foot">'
index_block = '''  <section class="panel-block index-block">
    <div class="block-head"><span>编号 / INDEX</span><span id="indexCount">31</span></div>
    <div id="indexList" class="index-list"></div>
  </section>

'''
if panel_foot not in h: raise SystemExit('panel foot not found')
h = h.replace(panel_foot, index_block + panel_foot)

# debug HUD before bottom bar
bottom = '<div id="bottom">'
coords = '''<div id="coordsHud" aria-live="off">
  <div><span>CAM</span><b id="dbgCam">X +000.0  Y +000.0  Z +000.0</b></div>
  <div><span>ANG</span><b id="dbgAng">HDG 000.0° / PITCH 00.0°</b></div>
  <div><span>GROUND</span><b id="dbgGround">X —  Z —</b></div>
  <div><span>SELECT</span><b id="dbgSel">—</b></div>
  <div class="coord-note">X→东 · Z→南 · 角度自北顺时针 · 原点 24.457256, 118.031006</div>
</div>

'''
if bottom not in h: raise SystemExit('bottom anchor missing')
h = h.replace(bottom, coords + bottom)
html.write_text(h, encoding='utf-8')
print('html updated')
