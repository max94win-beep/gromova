"""Собирает gromova-cms.svg: структуру слоёв для Figma без плагина.
Перетащить SVG в файл Figma -> появятся группы-разделы с текстовыми слоями (id = имя слоя)
и картинками. Дальше figma_sync.py читает их по именам."""
import json, os, base64, urllib.request, html as H
HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'content.json'), encoding='utf-8'))
UA = {'User-Agent': 'Mozilla/5.0'}

def fetch_small(url):
    """картинка с CDN образца в уменьшенном размере (Shopify: суффикс размера в имени файла)"""
    u = url.replace('_2048x2048', '_900x900')
    try:
        data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
    except Exception:
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    mime = 'image/png' if data[:4] == b'\x89PNG' else 'image/jpeg'
    return f'data:{mime};base64,' + base64.b64encode(data).decode()

IMG_SIZE = {'home.hero.image': (1200, 738), 'home.block.1.image': (560, 560), 'home.block.2.image': (560, 560),
            'about.block.1.image': (640, 480), 'about.block.2.image': (640, 480)}
COL_W = 1300; GAP = 140
parts = []; x = 0; total_h = 0
for sec, data in C.items():
    y = 0; els = []
    els.append(f'<text id="_title" x="0" y="{y+28}" font-family="Inter" font-weight="700" font-size="28">Раздел: {sec}</text>'); y += 50
    els.append(f'<text id="_hint" x="0" y="{y+12}" font-family="Inter" font-size="12" fill="#666">Меняйте текст в слоях и подменяйте картинки (Fill → Image). Имена слоёв не переименовывать.</text>'); y += 40
    for key, val in data.items():
        if key.endswith('.image') or key.endswith('ig.images'):
            vals = val if isinstance(val, list) else [val]
            for i, u in enumerate(vals):
                k = (key[:-1] + f'.{i+1}') if isinstance(val, list) else key   # ig.images -> ig.image.1
                w, h = IMG_SIZE.get(f'{sec}.{k}', (300, 300) if k.startswith('ig') else (400, 600))
                els.append(f'<text id="_label" x="0" y="{y+11}" font-family="Inter" font-size="11" fill="#888">{k}</text>'); y += 20
                els.append(f'<image id="{k}" x="0" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" href="{fetch_small(u)}"/>'); y += h + 24
                print('img', sec, k, flush=True)
        else:
            fs = 24 if key.endswith('title') else 14
            els.append(f'<text id="_label" x="0" y="{y+11}" font-family="Inter" font-size="11" fill="#888">{key}</text>'); y += 20
            els.append(f'<text id="{key}" x="0" y="{y+fs}" font-family="Inter" font-size="{fs}">{H.escape(str(val))}</text>'); y += fs + 22
    parts.append(f'<g id="{sec}" transform="translate({x},0)"><rect x="-32" y="-32" width="{COL_W}" height="{y+64}" fill="#f8f6f2"/>' + ''.join(els) + '</g>')
    x += COL_W + GAP; total_h = max(total_h, y + 64)
svg = f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{x}" height="{total_h}" viewBox="-32 -32 {x} {total_h}">' + ''.join(parts) + '</svg>'
out = os.path.join(HERE, '..', 'gromova-cms.svg')
open(out, 'w', encoding='utf-8').write(svg)
print('svg', os.path.getsize(out) // 1024, 'KB')
