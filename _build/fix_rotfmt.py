from pathlib import Path
p=Path(r'xmfls-osm-model\src\calibrate.html'); s=p.read_text(encoding='utf-8')
s=s.replace("slider('#rot','angle','#rotv',v=>((v%360)+360)%360.toFixed(1)+'°');", "slider('#rot','angle','#rotv',v=>(((v%360)+360)%360).toFixed(1)+'°');")
p.write_text(s,encoding='utf-8'); print('fixed')
