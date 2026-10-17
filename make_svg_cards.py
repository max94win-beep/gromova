"""SVG раздела cards для Figma: папка «Товар N» на каждый товар, внутри слои
image, image2, video, name, price, description, composition. Перетащить в файл Figma,
старую плоскую группу cards удалить."""
import json, os, base64, urllib.request, html as H
HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'content.json'), encoding='utf-8'))['cards']
UA = {'User-Agent': 'Mozilla/5.0'}
def img64(url):
    u = url.replace('_2048x2048', '_700x700')
    try: data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
    except Exception: data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    mime = 'image/png' if data[:4] == b'\x89PNG' else 'image/jpeg'
    return f'data:{mime};base64,' + base64.b64encode(data).decode()

FIELDS = ['image', 'image2', 'video', 'name', 'price', 'description', 'composition']
COL_W, ROW_H, COLS = 760, 1180, 4
groups = []
for i in range(1, 13):
    cx, cy = ((i - 1) % COLS) * (COL_W + 60), ((i - 1) // COLS) * (ROW_H + 80)
    y = 0; els = [f'<rect x="-24" y="-24" width="{COL_W}" height="{ROW_H}" fill="#f1ede6"/>',
                  f'<text id="_title" x="0" y="{y+26}" font-family="Inter" font-weight="700" font-size="26">Товар {i}</text>']
    y += 50
    for f in FIELDS:
        val = C.get(f'{i}.{f}', '')
        els.append(f'<text id="_label" x="0" y="{y+11}" font-family="Inter" font-size="11" fill="#888">{f}</text>'); y += 18
        if f in ('image', 'image2'):
            w, h = 330, 495
            x0 = 0 if f == 'image' else 350
            if f == 'image2': y -= 18 + 495 + 20   # второе фото рядом с первым
            els.append(f'<image id="{f}" x="{x0}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" href="{img64(val)}"/>')
            y += h + 20
            if f == 'image2': pass
        else:
            fs = 20 if f == 'name' else 14
            txt = val if val else ('https://… ссылка на видео (необязательно)' if f == 'video' else '')
            els.append(f'<text id="{f}" x="0" y="{y+fs}" font-family="Inter" font-size="{fs}">{H.escape(str(txt))}</text>'); y += fs + 18
    groups.append(f'<g id="Товар {i}" transform="translate({cx},{cy})">' + ''.join(els) + '</g>')
    print('card', i, flush=True)
W = COLS * (COL_W + 60); Hh = 3 * (ROW_H + 80)
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W+64}" height="{Hh+64}" viewBox="-32 -32 {W+64} {Hh+64}">'
       f'<g id="cards"><text id="_title" x="0" y="-40" font-family="Inter" font-weight="700" font-size="28">Раздел: cards (товары)</text>' + ''.join(groups) + '</g></svg>')
out = os.path.join(HERE, 'cards-import.svg'); open(out, 'w', encoding='utf-8').write(svg)
print('svg', os.path.getsize(out) // 1024, 'KB')
