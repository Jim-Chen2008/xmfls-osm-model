from pathlib import Path
p=Path(r'xmfls-osm-model\src\calibrate.html'); s=p.read_text(encoding='utf-8')
s=s.replace('id="rot" type="range" min="-180" max="180" step="0.1" value="-100.3"', 'id="rot" type="range" min="0" max="360" step="0.1" value="259.7"')
s=s.replace("img.angle=(img.angle+180)%360; if(img.angle>180)img.angle-=180;", "img.angle=((img.angle+180)%360+360)%360;")
s=s.replace("$('#reset').onclick=()=>{ Object.assign(img,DEFAULTS); $('#rot').value=img.angle;", "$('#reset').onclick=()=>{ Object.assign(img,DEFAULTS); $('#rot').value=((img.angle%360)+360)%360;")
p.write_text(s,encoding='utf-8'); print('patched sliders')
