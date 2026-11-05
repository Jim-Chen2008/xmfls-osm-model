from lxml import etree
from pathlib import Path
import math, json, datetime

SRC = Path(r'C:\Users\Jim\Downloads\map.osm')
OUT = Path(r'C:\xmfls test\ds\xmfls-osm-model\src\osm_model_data.js')
OUT.parent.mkdir(parents=True, exist_ok=True)

tree = etree.parse(str(SRC))
root = tree.getroot()
bounds_el = root.find('bounds')
minlat, maxlat, minlon, maxlon = map(float, (bounds_el.get('minlat'), bounds_el.get('maxlat'), bounds_el.get('minlon'), bounds_el.get('maxlon')))

nodes = {}
for n in root.findall('node'):
    if n.get('visible') == 'false':
        continue
    nodes[n.get('id')] = {
        'lat': float(n.get('lat')), 'lon': float(n.get('lon')),
        'tags': {t.get('k'): t.get('v') for t in n.findall('tag')}
    }

ways = {}
for w in root.findall('way'):
    if w.get('visible') == 'false':
        continue
    ways[w.get('id')] = {
        'refs': [nd.get('ref') for nd in w.findall('nd')],
        'tags': {t.get('k'): t.get('v') for t in w.findall('tag')}
    }

relations = {}
for r in root.findall('relation'):
    relations[r.get('id')] = {
        'members': [(m.get('type'), m.get('ref'), m.get('role')) for m in r.findall('member')],
        'tags': {t.get('k'): t.get('v') for t in r.findall('tag')}
    }

# local tangent projection around the OSM bounds centre
lat0 = (minlat + maxlat) / 2
lon0 = (minlon + maxlon) / 2
MPD = 111132.0
COSLAT = math.cos(math.radians(lat0))
def raw_xy(lat, lon):
    return ((lon - lon0) * MPD * COSLAT, (lat0 - lat) * MPD)

def raw_ring(w):
    pts = []
    for nid in w['refs']:
        if nid in nodes:
            n = nodes[nid]
            pts.append(raw_xy(n['lat'], n['lon']))
    # remove duplicate final vertex for processing
    if len(pts) > 1 and math.hypot(pts[0][0]-pts[-1][0], pts[0][1]-pts[-1][1]) < .01:
        pts.pop()
    return pts

def signed_area(pts):
    if len(pts) < 3: return 0
    s = 0
    for i, (x1, z1) in enumerate(pts):
        x2, z2 = pts[(i + 1) % len(pts)]
        s += x1 * z2 - x2 * z1
    return s / 2

def centroid(pts):
    a = signed_area(pts)
    if abs(a) < 1e-6:
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    cx = cz = 0
    for i, (x1, z1) in enumerate(pts):
        x2, z2 = pts[(i + 1) % len(pts)]
        cr = x1 * z2 - x2 * z1
        cx += (x1 + x2) * cr
        cz += (z1 + z2) * cr
    return (cx / (6 * a), cz / (6 * a))

def bbox(pts):
    xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
    return [min(xs), max(xs), min(zs), max(zs)]

def perimeter(pts):
    return sum(math.hypot(pts[i][0]-pts[(i+1)%len(pts)][0], pts[i][1]-pts[(i+1)%len(pts)][1]) for i in range(len(pts)))

def point_in_poly(pt, poly):
    x, z = pt
    inside = False
    for i in range(len(poly)):
        x1, z1 = poly[i]; x2, z2 = poly[(i + 1) % len(poly)]
        if ((z1 > z) != (z2 > z)) and (x < (x2 - x1) * (z - z1) / (z2 - z1) + x1):
            inside = not inside
    return inside

# select our school boundary (named 厦门外国语学校) from amenity=school ways
school_candidates = []
for wid, w in ways.items():
    if w['tags'].get('amenity') != 'school':
        continue
    pts = raw_ring(w)
    if len(pts) < 3:
        continue
    school_candidates.append((wid, w, pts))
our = None
for wid, w, pts in school_candidates:
    if '厦门外国语学校' in w['tags'].get('name', ''):
        our = (wid, w, pts)
        break
if our is None:
    # fall back to largest school polygon in the extract
    our = max(school_candidates, key=lambda q: abs(signed_area(q[2])))
school_id, school_way, school_raw = our
s_c = centroid(school_raw)
s_bb = bbox(school_raw)
origin_x = (s_bb[0] + s_bb[1]) / 2
origin_z = (s_bb[2] + s_bb[3]) / 2
school_lat = None
school_lon = None
# recover lat/lon of origin from average of boundary nodes (approximately) for display
lats = [nodes[nid]['lat'] for nid in school_way['refs'] if nid in nodes]
lons = [nodes[nid]['lon'] for nid in school_way['refs'] if nid in nodes]
school_lat = lat0 - origin_z / MPD
school_lon = lon0 + origin_x / (MPD * COSLAT)

def pt(x, z):
    return [round(x - origin_x, 2), round(z - origin_z, 2)]
def ring(pts):
    return [pt(x, z) for x, z in pts]

def feature(wid, w, pts, extra=None):
    a = abs(signed_area(pts))
    p = perimeter(pts)
    bb = bbox(pts)
    c = centroid(pts)
    d = {
        'id': wid,
        'tags': w['tags'],
        'polygon': ring(pts),
        'area': round(a, 1),
        'perimeter': round(p, 1),
        'bbox': [round(bb[0]-origin_x, 2), round(bb[1]-origin_x, 2), round(bb[2]-origin_z, 2), round(bb[3]-origin_z, 2)],
        'centroid': pt(c[0], c[1]),
        'vertices': len(pts)
    }
    if extra: d.update(extra)
    return d

# all buildings
buildings = []
for wid, w in ways.items():
    if 'building' not in w['tags']:
        continue
    pts = raw_ring(w)
    if len(pts) < 3:
        continue
    c = centroid(pts)
    inside = point_in_poly(c, school_raw)
    buildings.append(feature(wid, w, pts, {
        'inside': inside,
        'name': w['tags'].get('name'),
        'building': w['tags'].get('building'),
        'levels': w['tags'].get('building:levels'),
        'height': w['tags'].get('height'),
        'tourism': w['tags'].get('tourism')
    }))
buildings.sort(key=lambda b: (not b['inside'], b['centroid'][1], b['centroid'][0]))

# other school boundaries (context only)
other_schools = []
for wid, w, pts in school_candidates:
    if wid == school_id:
        continue
    other_schools.append(feature(wid, w, pts))

# school boundary as its own record
school = feature(school_id, school_way, school_raw)
school['name'] = school_way['tags'].get('name')
school['address'] = {k: v for k, v in school_way['tags'].items() if k.startswith('addr:')}

# leisure track relation
track = None
for rid, rel in relations.items():
    if rel['tags'].get('leisure') != 'track':
        continue
    outer = None; inner = None
    for typ, ref, role in rel['members']:
        if typ != 'way' or ref not in ways:
            continue
        pts = raw_ring(ways[ref])
        if len(pts) < 3: continue
        rec = feature(ref, ways[ref], pts)
        if role == 'outer': outer = rec
        elif role == 'inner': inner = rec
    track = {'id': rid, 'tags': rel['tags'], 'outer': outer, 'inner': inner}
    break

# leisure pitches (including the soccer pitch inner ring)
pitches = []
for wid, w in ways.items():
    if w['tags'].get('leisure') != 'pitch':
        continue
    pts = raw_ring(w)
    if len(pts) < 3: continue
    pitches.append(feature(wid, w, pts))

# roads
roads = []
for wid, w in ways.items():
    if 'highway' not in w['tags']:
        continue
    wpts = []
    for nid in w['refs']:
        if nid in nodes:
            n = nodes[nid]
            x, z = raw_xy(n['lat'], n['lon'])
            wpts.append(pt(x, z))
    if len(wpts) < 2: continue
    roads.append({
        'id': wid,
        'tags': w['tags'],
        'points': wpts,
        'name': w['tags'].get('name'),
        'highway': w['tags'].get('highway')
    })

# landuse polygons
landuse = []
for wid, w in ways.items():
    if 'landuse' not in w['tags']:
        continue
    pts = raw_ring(w)
    if len(pts) < 3: continue
    landuse.append(feature(wid, w, pts))

# barriers / fences
barriers = []
for wid, w in ways.items():
    if 'barrier' not in w['tags']:
        continue
    pts = [pt(*raw_xy(nodes[nid]['lat'], nodes[nid]['lon'])) for nid in w['refs'] if nid in nodes]
    if len(pts) >= 2:
        barriers.append({'id': wid, 'tags': w['tags'], 'points': pts})

# tagged points (bus stops, ATM, etc.) — context, not invented
points = []
for nid, n in nodes.items():
    if not n['tags']:
        continue
    if not any(k in n['tags'] for k in ('highway', 'amenity', 'tourism', 'shop', 'public_transport')):
        continue
    x, z = raw_xy(n['lat'], n['lon'])
    points.append({'id': nid, 'tags': n['tags'], 'point': pt(x, z)})

meta = {
    'source': 'map.osm',
    'sourcePath': str(SRC),
    'sourceBytes': SRC.stat().st_size,
    'generated': datetime.datetime.now().isoformat(timespec='seconds'),
    'origin': {'lat': round(school_lat, 7), 'lon': round(school_lon, 7)},
    'projection': 'local tangent, metres; +x east, +z south; origin = school-boundary bbox centre',
    'boundsOsm': {'minlat': minlat, 'maxlat': maxlat, 'minlon': minlon, 'maxlon': maxlon},
    'counts': {
        'nodes': len(nodes), 'ways': len(ways), 'relations': len(relations),
        'buildings': len(buildings), 'insideBuildings': sum(1 for b in buildings if b['inside']),
        'outsideBuildings': sum(1 for b in buildings if not b['inside']),
        'roads': len(roads), 'pitches': len(pitches), 'landuse': len(landuse)
    },
    'school': {
        'id': school_id,
        'name': school_way['tags'].get('name'),
        'area': school['area'],
        'perimeter': school['perimeter'],
        'bbox': school['bbox'],
        'tags': school_way['tags']
    }
}

data = {
    'meta': meta,
    'school': school,
    'otherSchools': other_schools,
    'buildings': buildings,
    'track': track,
    'pitches': pitches,
    'roads': roads,
    'landuse': landuse,
    'barriers': barriers,
    'points': points
}

js = "/* Generated directly from map.osm — OpenStreetMap contributors, ODbL.\n" \
     " * No other map, photo, or reference-site geometry is used.\n" \
     " * Building heights are NOT present in this OSM extract; the viewer uses a\n" \
     " * single adjustable schematic height.\n" \
     " */\nwindow.OSM_MODEL = " + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ";\n"
OUT.write_text(js, encoding='utf-8')

print('wrote', OUT, OUT.stat().st_size, 'bytes')
print('school', school_id, school_way['tags'].get('name'), 'area', school['area'], 'bbox', school['bbox'])
print('counts', meta['counts'])
print('track outer/inner vertices', len(track['outer']['polygon']) if track and track['outer'] else 0, len(track['inner']['polygon']) if track and track['inner'] else 0)
print('buildings inside/outside', meta['counts']['insideBuildings'], meta['counts']['outsideBuildings'])
print('roads', [(r['name'], r['highway']) for r in roads[:10]])
print('landuse', [l['tags'].get('landuse') for l in landuse])
print('points', [(p['tags'].get('highway'), p['tags'].get('name')) for p in points[:10]])
