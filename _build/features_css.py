from pathlib import Path
p = Path(r'xmfls-osm-model\src\style.css')
s = p.read_text(encoding='utf-8')
anchor = '/* ---------- responsive ---------- */'
css = r'''
/* ---------- feature index / numbers / debug ---------- */
.sw-extra{background:#c7d0bd;border:1px solid #8c9b84}
.sw-guide{background:#c78368;border:1px solid #9f604c}
.sw-num{background:#3f5d4b;color:#fff;font-size:7px;display:flex;align-items:center;justify-content:center;border-radius:50%;width:9px;height:9px}
.index-block{padding-bottom:8px}
#indexCount{font-family:var(--mono);font-size:9px;color:var(--accent);letter-spacing:.04em}
.index-list{max-height:178px;overflow:auto;margin:0 -4px;padding:0 4px 2px;scrollbar-width:thin;scrollbar-color:rgba(70,78,68,.25) transparent}
.index-list::-webkit-scrollbar{width:4px}
.index-list::-webkit-scrollbar-thumb{background:rgba(70,78,68,.2);border-radius:3px}
.idx-row{
  display:grid;grid-template-columns:30px 1fr auto;align-items:center;gap:5px;
  width:100%;border:0;background:transparent;border-bottom:1px solid rgba(45,54,46,.07);
  padding:5px 2px;text-align:left;color:var(--ink-soft);
}
.idx-row:hover{background:rgba(67,78,67,.055)}
.idx-row b{font-family:var(--mono);font-size:8.5px;color:var(--accent);font-weight:600}
.idx-row span{font-size:8.5px;line-height:1.2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.idx-row em{font-family:var(--mono);font-style:normal;font-size:7.5px;color:var(--muted)}
.idx-row i{grid-column:2 / 4;font-family:var(--mono);font-style:normal;font-size:7.5px;color:var(--muted);letter-spacing:.01em;margin-top:-1px}
.idx-row .idx-kind{color:var(--muted);font-size:7.5px;margin-left:4px}
.map-label.code{
  transform:translate(-50%,-50%);width:19px;height:19px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;padding:0;
  background:var(--green);color:#f7f1e4;border:1.5px solid rgba(250,247,239,.85);
  font-family:var(--mono);font-size:7.5px;font-weight:600;letter-spacing:0;
  box-shadow:0 2px 7px rgba(40,45,35,.22);backdrop-filter:none;
}
.map-label.code.outside{background:#8b8d84;font-size:7px}
.map-label.feature{font-size:8.5px;padding:3px 6px;color:var(--ink);background:rgba(252,247,237,.9)}
.map-label.feature b{font-family:var(--mono);color:var(--accent);font-size:7.5px;margin-right:3px}
#coordsHud{
  position:fixed;z-index:6;left:26px;top:158px;width:270px;
  background:rgba(34,44,36,.88);color:#dbe6d5;border:1px solid rgba(255,255,255,.09);
  border-radius:8px;padding:8px 10px 7px;
  font-family:var(--mono);font-size:8px;line-height:1.65;letter-spacing:.01em;
  box-shadow:0 9px 28px -18px rgba(20,30,20,.5);backdrop-filter:blur(10px);
  pointer-events:none;
}
#coordsHud>div{display:flex;gap:7px;white-space:nowrap}
#coordsHud span{width:38px;flex:0 0 38px;color:#8fa18d;letter-spacing:.06em;font-size:7px;padding-top:1px}
#coordsHud b{font-weight:500;color:#e2ebdc;font-size:8px}
#coordsHud b.hot{color:#efb18f}
#coordsHud .coord-note{display:block;color:#8b9b87;font-size:6.8px;line-height:1.5;margin-top:3px;border-top:1px solid rgba(255,255,255,.09);padding-top:4px;white-space:normal}
.map-label.code.hidden-code{display:none}
@media (max-width:1050px){
  #coordsHud{width:245px;font-size:7.5px}
}
@media (max-width:760px){
  #coordsHud{display:none}
  .index-list{max-height:150px}
}

'''
if anchor not in s: raise SystemExit('responsive anchor missing')
s = s.replace(anchor, css + anchor)
p.write_text(s, encoding='utf-8')
print('css updated')
