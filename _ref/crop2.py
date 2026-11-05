# -*- coding: utf-8 -*-
from PIL import Image

def crop(src, box, name, scale=2):
    im = Image.open(src).convert('RGB')
    c = im.crop(box)
    c = c.resize((int(c.width*scale), int(c.height*scale)), Image.LANCZOS)
    c.save(f'_ref/crop/{name}.png')
    print(name, c.size)

# gate_above 原图坐标 (原图 1156x2510, 照片区 y 900..1700, x 140..1140)
crop('_ref/gate_above.jpg', (380, 1290, 1140, 1560), 'gate_above_zoom', 2.2)
crop('_ref/gate_above.jpg', (140, 1290, 620, 1560), 'gate_above_left', 2.2)
crop('_ref/gate_above.jpg', (700, 1290, 1140, 1560), 'gate_above_right', 2.2)

# plaza 原图坐标
crop('_ref/plaza_view.jpg', (480, 1420, 1120, 1720), 'bed_zoom', 2.0)
crop('_ref/plaza_view.jpg', (400, 1440, 760, 1660), 'fountain_zoom', 3.0)
crop('_ref/plaza_view.jpg', (110, 1180, 720, 1420), 'gate_from_plaza', 2.0)

# gate front 细节
crop('_ref/gate_front.jpg', (20, 1020, 600, 1580), 'gate_front_left', 2.0)
crop('_ref/gate_front.jpg', (600, 1020, 1156, 1580), 'gate_front_right', 2.0)
