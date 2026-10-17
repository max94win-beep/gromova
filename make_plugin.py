"""Собирает Figma-плагин figma-plugin/ (manifest.json + code.js), который одной командой создаёт в файле Figma
страницу «Gromova CMS» со структурой слоёв по content.json: текстовые слои с текущими текстами и прямоугольники
с текущими картинками. После этого дизайнер правит тексты и подменяет картинки прямо в Figma,
а figma_sync.py забирает их на сайт."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, 'content.json'), encoding='utf-8'))
out = os.path.join(HERE, 'figma-plugin'); os.makedirs(out, exist_ok=True)

json.dump({
  "name": "Gromova CMS: создать структуру",
  "id": "gromova-cms-structure",
  "api": "1.0.0",
  "main": "code.js",
  "editorType": ["figma"],
  "networkAccess": {"allowedDomains": ["*"], "reasoning": "загрузка текущих фото сайта в макет"}
}, open(os.path.join(out, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# порядок и размеры картинок (px в макете) для каждого ключа
IMG_SIZE = {'home.hero.image': (1440, 885), 'home.block.1.image': (680, 680), 'home.block.2.image': (680, 680),
            'about.block.1.image': (800, 600), 'about.block.2.image': (800, 600)}
code = r'''
const CONTENT = %s;
const IMG_SIZE = %s;
function isImg(k){ return k.endsWith('.image') || k.endsWith('ig.images'); }
async function main(){
  await figma.loadFontAsync({family:"Inter", style:"Regular"});
  await figma.loadFontAsync({family:"Inter", style:"Bold"});
  const page = figma.createPage(); page.name = "Gromova CMS"; figma.currentPage = page;
  let y = 0;
  const sections = Object.keys(CONTENT);
  for (const sec of sections){
    const frame = figma.createFrame(); frame.name = sec; frame.x = 0; frame.y = y;
    frame.layoutMode = "VERTICAL"; frame.primaryAxisSizingMode = "AUTO"; frame.counterAxisSizingMode = "AUTO";
    frame.paddingTop = frame.paddingBottom = frame.paddingLeft = frame.paddingRight = 32; frame.itemSpacing = 16;
    frame.fills = [{type:"SOLID", color:{r:0.98,g:0.97,b:0.95}}];
    const title = figma.createText(); title.fontName={family:"Inter",style:"Bold"}; title.fontSize = 28; title.characters = "Раздел: " + sec; title.name = "_title"; frame.appendChild(title);
    const hint = figma.createText(); hint.fontSize = 12; hint.characters = "Меняйте текст в слоях и подменяйте картинки (Fill → Image). Имена слоёв не переименовывать."; hint.name = "_hint"; frame.appendChild(hint);
    const data = CONTENT[sec];
    for (const key of Object.keys(data)){
      const val = data[key];
      if (isImg(key)){
        const vals = Array.isArray(val) ? val : [val];
        for (let i=0;i<vals.length;i++){
          const k = Array.isArray(val) ? key.replace(/s$/, "") + "." + (i+1) : key;   // ig.images -> ig.image.1 ...
          const label = figma.createText(); label.fontSize = 11; label.characters = k; label.name = "_label"; frame.appendChild(label);
          const rect = figma.createRectangle(); rect.name = k;
          const [w,h] = IMG_SIZE[sec + "." + k] || (k.startsWith("ig") ? [300,300] : [400,600]);
          rect.resize(w, h);
          try { const img = await figma.createImageAsync(vals[i]); rect.fills = [{type:"IMAGE", scaleMode:"FILL", imageHash: img.hash}]; }
          catch(e){ rect.fills = [{type:"SOLID", color:{r:0.85,g:0.8,b:0.75}}]; }
          frame.appendChild(rect);
        }
      } else {
        const label = figma.createText(); label.fontSize = 11; label.characters = key; label.name = "_label"; frame.appendChild(label);
        const t = figma.createText(); t.name = key; t.fontSize = key.endsWith("title") ? 24 : 14;
        t.textAutoResize = "HEIGHT"; t.resize(900, 20); t.characters = String(val); frame.appendChild(t);
      }
    }
    y += frame.height + 120;
  }
  figma.viewport.scrollAndZoomIntoView(page.children);
  figma.notify("Структура Gromova CMS создана: " + sections.length + " разделов");
  figma.closePlugin();
}
main();
'''
# ключи вида "hero.image" внутри раздела home -> в плагине проверяем sec+"."+key
content_for_plugin = {sec: {k: v for k, v in d.items()} for sec, d in C.items()}
open(os.path.join(out, 'code.js'), 'w', encoding='utf-8').write(code % (json.dumps(content_for_plugin, ensure_ascii=False), json.dumps(IMG_SIZE)))
open(os.path.join(out, 'README.md'), 'w', encoding='utf-8').write('''# Gromova CMS — плагин для Figma

1. Открой нужный файл в Figma (desktop).
2. Меню → Plugins → Development → **Import plugin from manifest…** → выбери `manifest.json` из этой папки.
3. Plugins → Development → **Gromova CMS: создать структуру** → появится страница «Gromova CMS» с разделами.
4. Дальше просто редактируй тексты в слоях и подменяй картинки (выдели прямоугольник → Fill → Image).
   Имена слоёв не менять: по ним сайт забирает содержимое.
''')
print('plugin written to', out)
