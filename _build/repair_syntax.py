# -*- coding: utf-8 -*-
"""Repair remaining mojibake docstrings/comments until the file parses."""
import ast

p = r"C:\xmfls test\ds\xmfls-osm-model\_build\build_scene.py"
lines = open(p, encoding='utf-8-sig').read().splitlines()

def safe_comment(line):
    ind = len(line) - len(line.lstrip())
    body = line.strip()
    if body.startswith('#'):
        return ' ' * ind + '# ---'
    if body.startswith('"""') or body.startswith("'''"):
        q = body[:3]
        return ' ' * ind + q + 'ref' + q
    return None

for it in range(60):
    src = '\n'.join(lines) + '\n'
    try:
        ast.parse(src)
        print('parsed OK after', it, 'fixes')
        break
    except SyntaxError as e:
        ln = e.lineno - 1
        line = lines[ln] if 0 <= ln < len(lines) else ''
        rep = safe_comment(line)
        print('fix line', ln + 1, 'kind', ('doc' if rep and rep.strip().startswith(('"""', "'''")) else ('comment' if rep else 'other')))
        lines[ln] = rep if rep else (' ' * (len(line) - len(line.lstrip())) + '# ' + line.strip())
else:
    print('could not fix')
    raise SystemExit(1)

open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print('written')
