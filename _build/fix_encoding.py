# -*- coding: utf-8 -*-
import shutil

p = r"C:\xmfls test\ds\xmfls-osm-model\_build\build_scene.py"
s = open(p, encoding='utf-8').read().lstrip('\ufeff')
fixed = s.encode('gbk', errors='strict').decode('utf-8', errors='strict')
checks = ['大门_', '喷泉_', '黄色网格椭圆广场_200', '厦门外国语学校', '门卫房墩']
print({c: (c in fixed) for c in checks})
shutil.copyfile(p, p + '.mojibake')
open(p, 'w', encoding='utf-8').write(fixed)
print('restored, len', len(fixed))
