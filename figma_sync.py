"""Синхронизация содержимого сайта из Figma (Figma = CMS).
Читает файл Figma по REST API, собирает тексты и картинки из слоёв, названных по ключам
(например `home.hero.title`, `cards.3.image`), и записывает их в content.json; картинки — в img/.
Запуск: FIGMA_TOKEN=... FIGMA_FILE_KEY=... python3 figma_sync.py
Правила именования слоёв в Figma:
  - текстовый слой  "<раздел>.<ключ>"   -> текст (site.announcement, home.hero.title, cards.3.name, about.lead ...)
  - прямоугольник с картинкой "<раздел>.<ключ>.image" -> экспорт JPG 2x -> img/<раздел>.<ключ>.jpg
  - кадры (frames) верхнего уровня = разделы: site, nav, home, cards, novinki, bestsellery, katalog, about
Слои, которых нет в Figma, не трогаются (остаются как в content.json)."""
import json, os, re, sys, time, urllib.request, hashlib

TOKEN = os.environ.get('FIGMA_TOKEN'); KEY = os.environ.get('FIGMA_FILE_KEY')
if not TOKEN or not KEY: sys.exit('нужны FIGMA_TOKEN и FIGMA_FILE_KEY')
HERE = os.path.dirname(os.path.abspath(__file__))
API = 'https://api.figma.com/v1'
SECTIONS = {'site', 'nav', 'home', 'cards', 'novinki', 'bestsellery', 'katalog', 'about'}

def get(url):
    req = urllib.request.Request(url, headers={'X-Figma-Token': TOKEN})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
        except Exception as e:
            if attempt == 2: raise
            time.sleep(3)

doc = get(f'{API}/files/{KEY}')
content = json.load(open(os.path.join(HERE, 'content.json'), encoding='utf-8'))
texts, images = {}, {}   # key -> value / node id

def walk(node, section):
    name = (node.get('name') or '').strip()
    t = node.get('type')
    if section is None:
        if t in ('FRAME', 'SECTION', 'GROUP', 'COMPONENT') and name in SECTIONS:
            for ch in node.get('children', []): walk(ch, name)
        else:
            for ch in node.get('children', []): walk(ch, None)
        return
    key = name
    if key.startswith(section + '.'): key = key[len(section) + 1:]
    if key.startswith('_'):            # служебные подписи (_label, _title, _hint)
        pass
    elif t == 'TEXT' and re.match(r'^[\w.\-]+$', key):
        texts[(section, key)] = node.get('characters', '').strip()
    elif re.search(r'(^|\.)image(\.\d+)?$', key):   # hero.image, block.1.image, ig.image.3
        if any(f.get('type') == 'IMAGE' for f in node.get('fills', []) if isinstance(f, dict)):
            images[(section, key)] = node['id']
    for ch in node.get('children', []): walk(ch, section)

for page in doc['document'].get('children', []): walk(page, None)
print(f'Figma: текстов {len(texts)}, картинок {len(images)}; версия файла {doc.get("version")} от {doc.get("lastModified")}')

changed = 0
for (sec, key), val in texts.items():
    if val and content.setdefault(sec, {}).get(key) != val:
        content[sec][key] = val; changed += 1

if images:
    ids = ','.join(images.values())
    res = get(f'{API}/images/{KEY}?ids={ids}&format=jpg&scale=2')
    urls = res.get('images', {})
    os.makedirs(os.path.join(HERE, 'img'), exist_ok=True)
    for (sec, key), nid in images.items():
        u = urls.get(nid)
        if not u: continue
        data = urllib.request.urlopen(u, timeout=120).read()
        h = hashlib.md5(data).hexdigest()[:8]
        fn = f'img/{sec}.{key}.{h}.jpg'.replace('..', '.')
        fp = os.path.join(HERE, fn)
        if not os.path.exists(fp):
            for old in os.listdir(os.path.join(HERE, 'img')):
                if old.startswith(f'{sec}.{key}.'): os.remove(os.path.join(HERE, 'img', old))
            open(fp, 'wb').write(data)
        if content.setdefault(sec, {}).get(key) != fn:
            content[sec][key] = fn; changed += 1

json.dump(content, open(os.path.join(HERE, 'content.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('изменений:', changed)
