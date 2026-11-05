from pathlib import Path
p=Path(r'xmfls-osm-model\src\calibrate.html'); s=p.read_text(encoding='utf-8')
# defaults
s=s.replace("const DEFAULTS = { angle:260.3, scale:0.42, ax:-133, az:-35, opacity:0.72 };", "const DEFAULTS = { angle:260.3, scale:0.42, ax:-154.31, az:27.07, opacity:0.72 };")
# key markers
s=s.replace("{no:'25', name:'网球场A', x:-173, z:92},\n    {no:'26', name:'网球场B', x:-173, z:128},\n    {no:'27', name:'主席台', x:-133.5, z:61.5},\n    {no:'28', name:'平台', x:-77, z:-35},", "{no:'25', name:'网球场A', x:-156.11, z:70.18},\n    {no:'26', name:'网球场B', x:-156.11, z:103.07},\n    {no:'27', name:'主席台', x:-115.04, z:60.68},\n    {no:'28', name:'平台', x:-79.06, z:-38.45},")
s=s.replace("{no:'30', name:'喷泉', x:160, z:-128},\n    {no:'31', name:'校界', x:0, z:-153}", "{no:'30', name:'喷泉', x:105.93, z:-70.41},\n    {no:'31', name:'校界', x:0, z:-153},\n    {no:'32', name:'黄网格广场', x:130.5, z:-80.03}")
# import UI after block-title
old='      <div class="block-title"><span>实景图层</span><span id="alignInfo">R 260.3° / S 0.42</span></div>'
new=old+'''\n      <div class="import-row"><input id="paramText" type="text" value="angle=260.3, scale=0.420, anchor=-154.31,27.07" spellcheck="false"><button id="applyParams" class="primary">导入参数</button></div>
      <div class="step-note">格式：angle=260.3, scale=0.420, anchor=-154.31,27.07</div>'''
if old not in s: raise SystemExit('align title missing')
s=s.replace(old,new)
# css
s=s.replace(".step-note{font:7px/1.3 var(--mono);color:var(--muted);margin-top:5px;letter-spacing:.02em}", ".step-note{font:7px/1.3 var(--mono);color:var(--muted);margin-top:5px;letter-spacing:.02em}\n  .import-row{display:flex;gap:5px;margin:7px 0 2px}\n  .import-row input{flex:1;min-width:0;background:rgba(255,255,255,.65);border:1px solid var(--line);border-radius:4px;padding:5px 6px;font:7px/1.2 var(--mono);color:var(--ink);outline:none}\n  .import-row input:focus{border-color:rgba(63,93,75,.8)}")
# copy params exact + import handler
s=s.replace("$('#copyParams').onclick=()=>copyText(`angle=${img.angle.toFixed(1)}, scale=${img.scale.toFixed(3)}, anchor=${img.ax.toFixed(2)},${img.az.toFixed(2)}`);", "$('#copyParams').onclick=()=>copyText(`angle=${img.angle.toFixed(1)}, scale=${img.scale.toFixed(3)}, anchor=${img.ax.toFixed(2)},${img.az.toFixed(2)}`);")
anchor="$('#reset').onclick=()=>{"
apply=r'''  function applyParams(text){
    const num = (re) => { const m = text.match(re); return m ? parseFloat(m[1]) : null; };
    const a = num(/angle\s*=\s*(-?\d+(?:\.\d+)?)/i);
    const sc = num(/scale\s*=\s*(-?\d+(?:\.\d+)?)/i);
    const an = text.match(/anchor\s*=\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/i);
    if(a===null||sc===null||!an){ toast('格式不对：angle=…, scale=…, anchor=…,…'); return; }
    img.angle=((a%360)+360)%360;
    img.scale=Math.min(1.5,Math.max(.2,sc));
    img.ax=parseFloat(an[1]); img.az=parseFloat(an[2]);
    $('#paramText').value=`angle=${img.angle.toFixed(1)}, scale=${img.scale.toFixed(3)}, anchor=${img.ax.toFixed(2)},${img.az.toFixed(2)}`;
    syncParams(); draw(); toast('已导入对齐参数');
  }
  $('#applyParams').onclick=()=>applyParams($('#paramText').value);
  $('#paramText').addEventListener('keydown', e=>{ if(e.key==='Enter'){ e.preventDefault(); applyParams(e.target.value); } });
  '''
if anchor not in s: raise SystemExit('reset anchor missing')
s=s.replace(anchor, apply+anchor)
p.write_text(s,encoding='utf-8'); print('calibration updated')
