from pathlib import Path
import re, base64

root = Path(r'xmfls-osm-model')
src = root / 'src'
dist = root / 'dist'
dist.mkdir(exist_ok=True)
html = (src / 'index.html').read_text(encoding='utf-8')
css = (src / 'style.css').read_text(encoding='utf-8')
data = (src / 'osm_model_data.js').read_text(encoding='utf-8')
app = (src / 'app.js').read_text(encoding='utf-8')
three = (root / 'lib' / 'three.min.js').read_text(encoding='utf-8')
calib_path = dist / '坐标校准-实景叠图.html'
calib_b64 = base64.b64encode(calib_path.read_bytes()).decode('ascii') if calib_path.exists() else ''


def esc(js):
    return js.replace('</script', '<\\/script')


html = html.replace('<link rel="stylesheet" href="style.css">', '<style>\n' + css + '\n</style>')
block = '<script src="../lib/three.min.js"></script>\n<script src="osm_model_data.js"></script>\n<script src="app.js"></script>'
if block not in html:
    raise SystemExit('external script block not found')
calib_script = ''
if calib_b64:
    calib_script = '<script>window.__CALIB_PAGE="data:text/html;base64,' + calib_b64 + '";</script>\n'
inline = (
    '<!-- Three.js r128 (MIT), inlined for offline use -->\n'
    '<script>\n' + esc(three) + '\n</script>\n'
    '<script>\n/* OSM data extracted from map.osm. OpenStreetMap contributors, ODbL. */\n' + esc(data) + '\n</script>\n'
    + calib_script +
    '<script>\n' + esc(app) + '\n</script>'
)
html = html.replace(block, inline)
out = dist / '厦门外国语学校海沧校区-OSM模型.html'
out.write_text(html, encoding='utf-8')
print('wrote', out, out.stat().st_size, 'bytes', 'calib_embedded=', bool(calib_b64))
print('remaining external:', re.findall(r'<script[^>]+src=|<link[^>]+href="(?!data:)', html))
