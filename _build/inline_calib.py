from pathlib import Path
import base64, re
src = Path(r'xmfls-osm-model\src')
outdir = Path(r'xmfls-osm-model\dist')
outdir.mkdir(exist_ok=True)
html = (src / 'calibrate.html').read_text(encoding='utf-8')
data = (src / 'osm_model_data.js').read_text(encoding='utf-8')
photo = base64.b64encode((src / 'calib_photo.jpg').read_bytes()).decode('ascii')
data_uri = 'data:image/jpeg;base64,' + photo

def esc(js):
    return js.replace('</script', '<\\/script')

html = html.replace('<script src="osm_model_data.js"></script>',
                    '<script>\n/* OSM data © OpenStreetMap contributors, ODbL. */\n' + esc(data) + '\n</script>')
html = html.replace("photo.src = 'calib_photo.jpg';", "photo.src = '" + data_uri + "';")
out = outdir / '坐标校准-实景叠图.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, out.stat().st_size)
print('external assets:', re.findall(r'<script[^>]+src=|<link[^>]+href="(?!data:)', html))
