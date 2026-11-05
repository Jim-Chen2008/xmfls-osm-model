from pathlib import Path
src=Path(r'C:\xmfls test\ds\xmfls-osm-model\dist\厦门外国语学校海沧校区-OSM模型.html')
s=src.read_text(encoding='utf-8')
s=s.replace('</body>','<script>setTimeout(function(){var b=document.querySelector("#editToggle"); if(b)b.click(); var o=document.querySelector("#overlayBtn"); if(o)o.click();},1200);</script></body>')
out=src.with_name('_inspect_final_overlay.html'); out.write_text(s,encoding='utf-8'); print(out, out.stat().st_size)
