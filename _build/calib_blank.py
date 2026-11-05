from pathlib import Path
p=Path(r'xmfls-osm-model\src\calibrate.html'); s=p.read_text(encoding='utf-8')
s=s.replace('<label class="check"><input id="gateOn" type="checkbox" checked>大门参考线</label>',
            '<label class="check"><input id="gateOn" type="checkbox" checked>大门参考线</label>\n        <label class="check"><input id="blankOn" type="checkbox">空白图层（仅坐标）</label>')
s=s.replace("const img = { ...DEFAULTS, on:true, osm:true, bld:true, grid:true, nums:true, gate:true };",
            "const img = { ...DEFAULTS, on:true, osm:true, bld:true, grid:true, nums:true, gate:true, blank:false };")
s=s.replace("  function draw(){\n    ctx.clearRect(0,0,W,H);\n    ctx.fillStyle='#f4efe5'; ctx.fillRect(0,0,W,H);\n    if(img.on) drawImage();\n    drawOsm();\n    if(img.grid) drawGrid();\n    drawGate();\n    drawKey();\n    drawMarkers();",
            "  function draw(){\n    ctx.clearRect(0,0,W,H);\n    ctx.fillStyle='#f4efe5'; ctx.fillRect(0,0,W,H);\n    if(img.blank){\n      if(img.grid) drawGrid();\n      drawMarkers();\n      return;\n    }\n    if(img.on) drawImage();\n    drawOsm();\n    if(img.grid) drawGrid();\n    drawGate();\n    drawKey();\n    drawMarkers();")
s=s.replace("  bind('#imgOn','on'); bind('#osmOn','osm'); bind('#bldOn','bld'); bind('#gridOn','grid'); bind('#numOn','nums'); bind('#gateOn','gate');",
            "  bind('#imgOn','on'); bind('#osmOn','osm'); bind('#bldOn','bld'); bind('#gridOn','grid'); bind('#numOn','nums'); bind('#gateOn','gate'); bind('#blankOn','blank');")
p.write_text(s,encoding='utf-8'); print('blank layer added')
