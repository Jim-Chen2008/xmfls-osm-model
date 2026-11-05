from pathlib import Path
p=Path(r'xmfls-osm-model\_build\parse_osm_model.py'); s=p.read_text(encoding='utf-8')
s=s.replace("s_c = centroid(school_raw)\norigin_x, origin_z = s_c", "s_c = centroid(school_raw)\ns_bb = bbox(school_raw)\norigin_x = (s_bb[0] + s_bb[1]) / 2\norigin_z = (s_bb[2] + s_bb[3]) / 2")
s=s.replace("school_lat = sum(lats) / len(lats)\nschool_lon = sum(lons) / len(lons)", "school_lat = lat0 - origin_z / MPD\nschool_lon = lon0 + origin_x / (MPD * COSLAT)")
s=s.replace("'projection': 'local tangent, metres; +x east, +z south; origin = school-boundary centroid',", "'projection': 'local tangent, metres; +x east, +z south; origin = school-boundary bbox centre',")
p.write_text(s,encoding='utf-8')
print('patched origin')
