import json,re
from pathlib import Path
P=Path(__file__).resolve().parent
G=json.loads((P/'guion.json').read_text(encoding='utf-8'))
TL=json.loads((P/'timeline.json').read_text(encoding='utf-8'))
M=json.loads((P/'_prep/assets_final.json').read_text(encoding='utf-8'))
def mm(t):return f'{int(t)//60:02}:{int(t)%60:02}'
chapters=[];last=None
for s,t in zip(G['scenes'],TL['timeline']):
    if s['chapter']!=last:
        title=s['chapter'].split('. ',1)[1].title().replace("'S", "'s")
        chapters.append(mm(t['start'])+' '+title);last=s['chapter']
description='''Why did Ukraine attack Russian ships in Libya? The Benghazi strike connects naval drones, Russia's African supply network and the political cost of taking the war beyond the Black Sea.

We explain the attack on the corvette Merkury and cargo ship Angara, Libya's divided authorities, Russia's relationship with Haftar, Africa Corps, the changing role of Tartus, and the dispute over prior coordination with European partners.

This account reflects information available on 28 November 2026. Claims about the operation are attributed to the officials making them. Angara is a dry cargo ship; its sinking is not confirmed. Animated scenes are reconstructions, and conceptual links are not verified voyage tracks.

CHAPTERS
'''+ '\n'.join(chapters)+'''

SOURCES
SBU statement, 23 November 2026 (Ukraine's account of the operation):
https://ssu.gov.ua/en/novyny/syly-oborony-ukrainy-spilno-z-sbu-znyshchyly-rosiiskyi-viiskovyi-korvet-merkurii-ta-urazyly-pidsanktsiine-sudno-rf-bilia-portu-benhazi-liviia

Associated Press, 25 November 2026 (Libyan officers and reactions):
https://apnews.com/article/russia-ukraine-war-libya-drone-attack-warship-officers-5719d6750c0619695c7f23a373cecd7b

Reuters, 27 November 2026 (capsized corvette and separate convoy):
https://www.internazionale.it/ultime-notizie-reuters/2026/11/27/exclusive-russian-military-flotilla-bound-for-libya-turns-around-after-warship-sunk-on-nov-22-sources-says

Reuters, 28 November 2026 (European coordination clarification):
https://www.internazionale.it/ultime-notizie-reuters/2026/11/28/ukraine-s-attack-on-russian-ship-in-libya-was-not-coordinated-with-partners-zelenskiy-says

ECFR, 28 March 2025 (Russia's Libyan network):
https://ecfr.eu/publication/the-bear-who-came-to-tea-russia-libya-and-the-kremlins-playbook-for-fragile-states/

Associated Press, 11 June 2025 (military shipping to Africa):
https://www.ap.org/news-highlights/spotlights/2025/russia-skirts-western-sanctions-to-ramp-up-its-military-footprint-in-africa/

Associated Press, 9 August 2026 (Syrian base agreement):
https://apnews.com/article/syria-russia-latakia-tartus-bases-hmeimem-deal-2ade8e8a7da23eae4a90c8070f002a86

Maps: Natural Earth. Illustrations and animated reconstructions: WarMap Stick, created with AI assistance and edited for this video.

#Ukraine #Libya #Russia
'''
tags='Ukraine Libya,Russia Libya,Benghazi attack,Merkury corvette,Angara ship,Ukraine naval drones,naval drone attack,Ukraine Russia war explained,Russia Africa Corps,Haftar,Libya explained,Russia Africa,Tartus,Syria Russian bases,Mediterranean,Russian military logistics,Black Sea drones,WarMap Stick,geopolitics explained'
assert len(tags)<=500
assert len(description)<=5000
text=f'''# Paquete de subida — Video 8: Libya

## TITLE

Why Ukraine Struck Russian Ships in Libya

Alternativa 1: Why Russia's Ships Were Vulnerable in Libya

Alternativa 2: How Libya Became Part of the Russia-Ukraine War

## DESCRIPTION

{description}
## TAGS

{tags}

{len(tags)} caracteres, incluidos espacios y comas.

## PINNED COMMENT

Should military supply routes remain targets wherever they lead, even through another country's ports? Where would you draw the line? Please keep the discussion focused on the evidence and the people affected. If you spot a factual error, share a dated source so we can check it.

## Test & Compare: orden de las tres miniaturas

Mantener el título principal fijo durante la prueba para comparar las imágenes. El orden es una recomendación editorial; no representa un resultado medido de CTR ni de retención.

1. **01_Libya.png — LIBYA?!** Ataque y sorpresa geográfica. Promesa más inmediata y coherente con el hook. Archivo: `Miniatura/Libya/01_Libya.png`.
2. **02_Russia_lifeline.png — RUSSIA’S LIFELINE** Red logística y consecuencias africanas. La cadena representa vulnerabilidad y daño local; el vídeo no afirma el colapso de toda la red. Archivo: `Miniatura/Libya/02_Russia_lifeline.png`.
3. **03_This_far.png — THIS FAR?** Alcance y contraste entre dron y buque. No representa una ruta de lanzamiento conocida. Archivo: `Miniatura/Libya/03_This_far.png`.

Las tres imágenes finales son PNG de 1280 × 720. Generadas con la herramienta integrada ImageGen; las variantes 2 y 3 recibieron una corrección de fondo para eliminar geografía errónea. Revisión cualitativa visual, sin puntuaciones de pago ni predicción de rendimiento.

'''
for n in range(1,4):
    v=M[f'thumb{n}'];text+=f"### Prompt {n}\n\n{v['prompt']}\n\n"
    if v.get('editPrompt'):text+=f"Corrección aplicada:\n\n{v['editPrompt']}\n\n"
text+='''## Entregables y uso

- `Render/Video8_Libya.mp4`: máster, 1920 × 1080, 30 fps; sonoridad objetivo −14 LUFS.
- `Render/Video8_upload.mp4`: copia ligera ≤10 MB, codificación en dos pasadas. Es una vista previa comprimida; usar el máster para la publicación final en YouTube.
- `Render/Video8_Libya.srt`: subtítulos ingleses temporizados desde las marcas de palabra de Ryan.
- `_prep/chk_000.jpg` a `_prep/chk_005.jpg`: control de los primeros seis segundos.
- `_prep/sheet.jpg`: fotograma cada 30 segundos.
- `_prep/verification.json`: medidas finales de archivos, duración, resolución y sonoridad.

El guion tiene 2166 palabras habladas y 175 escenas con frases completas. Primera frase: “Ukraine strikes Russia, in Libya.” (5 palabras). Síntesis: `Scripts/voz.py`, en-GB-RyanNeural, +4 %, como V7; ajuste posterior de tempo sin alterar el tono para un montaje de 15:00. Sin titular superior, sin karaoke, sin cajas negras y sin cartelas de capítulo.

## Fuentes completas de trabajo

'''
data=(P/'Datos (Codex).md').read_text(encoding='utf-8')
text+=data.split('## Fuentes consultadas',1)[1].split('## Cronología',1)[0].strip()+'\n'
(P/'Paquete de subida (Codex).md').write_text(text,encoding='utf-8')
(P/'descripcion_final.txt').write_text(description,encoding='utf-8')
print('description',len(description),'tags',len(tags),'chapters',chapters)
