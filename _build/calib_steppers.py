from pathlib import Path
p = Path(r'xmfls-osm-model\src\calibrate.html')
s = p.read_text(encoding='utf-8')

# CSS for fine-tune buttons
s = s.replace(".row label{font-size:9px;color:var(--soft);flex:0 0 56px}",
              ".row label{font-size:9px;color:var(--soft);flex:0 0 42px}\n  .step{width:22px;height:22px;padding:0;flex:0 0 22px;display:flex;align-items:center;justify-content:center;font:500 14px/1 var(--mono);color:var(--soft);border-radius:4px;background:rgba(255,255,255,.65)}\n  .step:hover{color:var(--ink);background:#fff}\n  .step:active{background:#e8e0d2}\n  .step-note{font:7px/1.3 var(--mono);color:var(--muted);margin-top:5px;letter-spacing:.02em}")

# defaults / displayed values
s = s.replace("R 259.7° / S 0.38", "R 260.3° / S 0.42")
s = s.replace('id="rot" type="range" min="0" max="360" step="0.1" value="259.7"', 'id="rot" type="range" min="0" max="360" step="0.1" value="260.3"')
s = s.replace('id="rotv">259.7°', 'id="rotv">260.3°')
s = s.replace('id="scl" type="range" min="0.2" max="1.5" step="0.005" value="0.38"', 'id="scl" type="range" min="0.2" max="1.5" step="0.005" value="0.42"')
s = s.replace('id="sclv">0.380', 'id="sclv">0.420')
s = s.replace("const DEFAULTS = { angle:259.7, scale:0.38, ax:-133, az:-35, opacity:0.74 };",
              "const DEFAULTS = { angle:260.3, scale:0.42, ax:-133, az:-35, opacity:0.72 };")

# rows with steppers
s = s.replace(
 '      <div class="row"><label>旋转</label><input id="rot" type="range" min="0" max="360" step="0.1" value="260.3"><span class="val" id="rotv">260.3°</span></div>\n'
 '      <div class="row"><label>缩放</label><input id="scl" type="range" min="0.2" max="1.5" step="0.005" value="0.42"><span class="val" id="sclv">0.420</span></div>\n'
 '      <div class="row"><label>透明度</label><input id="opa" type="range" min="0.1" max="1" step="0.01" value="0.72"><span class="val" id="opav">0.72</span></div>',
 '      <div class="row"><label>旋转</label><button class="step" data-key="rot" data-dir="-1" title="旋转 -0.1°">−</button><input id="rot" type="range" min="0" max="360" step="0.1" value="260.3"><button class="step" data-key="rot" data-dir="1" title="旋转 +0.1°">+</button><span class="val" id="rotv">260.3°</span></div>\n'
 '      <div class="row"><label>缩放</label><button class="step" data-key="scl" data-dir="-1" title="缩放 -0.005">−</button><input id="scl" type="range" min="0.2" max="1.5" step="0.005" value="0.42"><button class="step" data-key="scl" data-dir="1" title="缩放 +0.005">+</button><span class="val" id="sclv">0.420</span></div>\n'
 '      <div class="row"><label>透明度</label><button class="step" data-key="opa" data-dir="-1" title="透明度 -0.01">−</button><input id="opa" type="range" min="0.1" max="1" step="0.01" value="0.72"><button class="step" data-key="opa" data-dir="1" title="透明度 +0.01">+</button><span class="val" id="opav">0.72</span></div>\n'
 '      <div class="step-note">+/− 单步：旋转 0.1° · 缩放 0.005 · 透明度 0.01</div>')

# replace slider/reset/flip logic with shared sync + steppers
old = """  const slider=(id, key, out, fmtv)=>{
    const el=$(id); el.oninput=()=>{ img[key]=parseFloat(el.value); $(out).textContent=fmtv(img[key]); $('#alignInfo').textContent=`R ${img.angle.toFixed(1)}° / S ${img.scale.toFixed(2)}`; draw(); };
  };
  slider('#rot','angle','#rotv',v=>v.toFixed(1)+'°');
  slider('#scl','scale','#sclv',v=>v.toFixed(3));
  slider('#opa','opacity','#opav',v=>v.toFixed(2));
  $('#reset').onclick=()=>{ Object.assign(img,DEFAULTS); $('#rot').value=((img.angle%360)+360)%360; $('#scl').value=img.scale; $('#opa').value=img.opacity; $('#rotv').textContent=img.angle.toFixed(1)+'°'; $('#sclv').textContent=img.scale.toFixed(3); $('#opav').textContent=img.opacity.toFixed(2); draw(); };
  $('#flip').onclick=()=>{ img.angle=(img.angle+180)%360; if(img.angle>180)img.angle-=360; $('#rot').value=img.angle; $('#rotv').textContent=img.angle.toFixed(1)+'°'; draw(); };"""
new = """  const stepMeta = {
    rot: { key:'angle',  delta:0.1,   min:0,   max:360 },
    scl: { key:'scale',  delta:0.005, min:0.2, max:1.5 },
    opa: { key:'opacity',delta:0.01,  min:0.1, max:1 }
  };
  function syncParams(){
    const a = ((img.angle%360)+360)%360;
    $('#rot').value = a; $('#scl').value = img.scale; $('#opa').value = img.opacity;
    $('#rotv').textContent = a.toFixed(1)+'°';
    $('#sclv').textContent = img.scale.toFixed(3);
    $('#opav').textContent = img.opacity.toFixed(2);
    $('#alignInfo').textContent = `R ${a.toFixed(1)}° / S ${img.scale.toFixed(2)}`;
  }
  const slider=(id, key, out, fmtv)=>{
    const el=$(id); el.oninput=()=>{ img[key]=parseFloat(el.value); $(out).textContent=fmtv(img[key]); $('#alignInfo').textContent=`R ${img.angle.toFixed(1)}° / S ${img.scale.toFixed(2)}`; draw(); };
  };
  slider('#rot','angle','#rotv',v=>((v%360)+360)%360.toFixed(1)+'°');
  slider('#scl','scale','#sclv',v=>v.toFixed(3));
  slider('#opa','opacity','#opav',v=>v.toFixed(2));
  $$('.step').forEach(btn => {
    btn.onclick = () => {
      const meta = stepMeta[btn.dataset.key];
      const dir = Number(btn.dataset.dir);
      let v = img[meta.key] + meta.delta * dir;
      if(meta.key === 'angle') v = ((v%360)+360)%360;
      else v = Math.min(meta.max, Math.max(meta.min, v));
      img[meta.key] = v;
      syncParams(); draw();
    };
  });
  $('#reset').onclick=()=>{ Object.assign(img,DEFAULTS); syncParams(); draw(); };
  $('#flip').onclick=()=>{ img.angle=((img.angle+180)%360+360)%360; syncParams(); draw(); };"""
if old not in s:
    raise SystemExit('logic anchor missing')
s = s.replace(old, new)

# $$ helper isn't defined in the calibration page; add it
s = s.replace("const $ = s => document.querySelector(s);", "const $ = s => document.querySelector(s);\n  const $$ = s => Array.from(document.querySelectorAll(s));")

p.write_text(s, encoding='utf-8')
print('steppers added')
