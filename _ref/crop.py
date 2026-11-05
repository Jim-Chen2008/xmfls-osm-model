# -*- coding: utf-8 -*-
from PIL import Image
import os

os.makedirs('_ref/crop', exist_ok=True)

def crop(src, box, name, scale=2):
    im = Image.open(src).convert('RGB')
    c = im.crop(box)
    c = c.resize((c.width*scale, c.height*scale), Image.LANCZOS)
    c.save(f'_ref/crop/{name}.png')
    print(name, c.size)

# 全照片区域
crop('_ref/gate_front.jpg', (20, 1025, 1140, 1570), 'gate_full', 1)
crop('_ref/plaza_view.jpg', (20, 890, 1140, 1690), 'plaza_full', 1)
crop('_ref/gate_above.jpg', (140, 900, 1140, 1700), 'gate_above_full', 1)

# 细节
crop('_ref/gate_front.jpg', (240, 1180, 980, 1420), 'gate_letters', 2)
crop('_ref/gate_front.jpg', (150, 1030, 1140, 1210), 'gate_top', 2)
crop('_ref/gate_front.jpg', (180, 1190, 360, 1500), 'gate_left', 3)
crop('_ref/gate_front.jpg', (830, 1150, 1140, 1540), 'gate_right', 2)
crop('_ref/plaza_view.jpg', (330, 1380, 1000, 1630), 'plaza_fountain', 2)
crop('_ref/plaza_view.jpg', (560, 1380, 980, 1650), 'plaza_bed', 2)
