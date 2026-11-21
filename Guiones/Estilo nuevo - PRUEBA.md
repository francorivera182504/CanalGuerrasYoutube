# Estilo nuevo WarMap Stick: paquete de prueba

Basado en dos referencias:
- **Menuda Historia**, «La historia COMPLETA de CHINA con dibujitos»: 153k vistas.
- **Relatos Pintados**, «POV: Lavas Dinero Abriendo Un Hotel»: 37k vistas.

**Objetivo de esta prueba:** generar estas 7 imágenes primero para validar el estilo y el personaje antes de producir ~100 imágenes. Si el personaje sale bien en la imagen 1, esa imagen se usa como **referencia** en todas las demás.

---

## Qué cambia respecto al estilo anterior

| | Antes (video 10k) | Ahora (referencias) |
|---|---|---|
| Estilo | Íconos de línea negra, sin color | Caricatura 2D plana a color, tonos tierra suaves |
| Personajes | Pictogramas | Muñequitos de cabeza blanca redonda, ojos de punto, ropa de época |
| Formato | Cuadrado 1:1 | Horizontal 16:9 |
| Ritmo | ~10 s por imagen | **3–6 s por visual** |
| Mapas | Contornos de íconos | Mapa tipo pergamino con territorios a color, rutas punteadas que se dibujan y etiquetas que aparecen |
| Movimiento | Zoom simple | Personajes que entran, etiquetas que aparecen y mapas que se colorean |
| Hilo conductor | Ninguno | **Un personaje que se repite** (en China es «Wang», el campesino) |

**Cómo lo producimos:**
1. **Imágenes de IA (Higgsfield):** escenas con personajes y fondos, unas 45–50 por video de 6 min.
2. **Mapas y textos hechos por mí con código:** mapas pergamino que se colorean, flechas y rutas animadas, fechas y etiquetas que aparecen. Así sale como en Menuda Historia, que dice que su animación está «hecha a mano con código».
3. **Montaje con ffmpeg:** cada imagen tiene movimiento (entra, rebota, zoom suave), con efectos de sonido (whoosh, pop) y música.

---

## Personaje del canal: «Stick» 🪖

Es el reportero de guerra del canal y aparece en todos los videos, como Wang en el de China. Le da identidad a WarMap Stick y hace que la gente reconozca el canal.

---

## Bloque de estilo
Pégalo una vez al inicio del chat en Claude chat o Cowork.

```
Generate each of the following images with Higgsfield (nano_banana_2 or nano_banana_pro, 16:9, use unlimited generations). Use exactly this art style for ALL images:
2D flat vector cartoon illustration, clean thin consistent black outlines, flat colors with very soft shading, muted earthy palette (beige, tan, olive green, dusty red, soft sky blue, warm brown), soft gradient skies, simple clean backgrounds. Characters are simple cartoon people with big round white heads, small black dot eyes, simple line mouths, rosy cheeks, simple bodies wearing period-accurate clothing and uniforms. Friendly educational explainer look, like a modern history cartoon channel. No gore, no blood. No text unless the prompt asks for it. Leave some empty space for captions.
```

---

## Las 7 imágenes de prueba

**1. Hoja de personaje de Stick.** Es la más importante: si sale bien, la usamos de referencia.
```
1. Character reference sheet of the same cartoon character shown three times side by side on a plain beige background: front view, three-quarter view, and pointing at something. He is a war correspondent: big round white head, small black dot eyes, rosy cheeks, friendly confident smile, olive-green military helmet with a small white "PRESS" label, dark blue flak vest with "PRESS" written on the chest, light khaki shirt, brown cargo pants, brown boots, a small notebook in one hand.
```

**2. Video Irán: mapa con Stick explicando**
```
2. Stick (the war correspondent character from image 1) standing on the right side pointing with a stick at a large parchment-style map of the Middle East on the left: tan land, soft blue sea, thick brown borders, Iran filled in dusty red, the narrow Strait of Hormuz highlighted with a dashed circle. Warm, educational mood.
```

**3. Video Irán: Estrecho de Ormuz**
```
3. Wide scene of a narrow sea strait at sunset with soft orange gradient sky, a long line of large cargo ships and oil tankers stopped and waiting on calm blue water, small navy warships in the distance, on a small boat in the foreground Stick (character from image 1) looking at them through binoculars with a worried face.
```

**4. Video Irán: oficinas de poder (sin caras reales)**
```
4. Split scene: on the left a generic white government building with columns and a cartoon official in a dark suit at a desk on the phone; on the right a generic Middle Eastern government building with a dome and a cartoon official in a grey suit on the phone; a jagged red lightning line between them showing tension.
```

**5. Video Vietnam: selva**
```
5. Dense green jungle scene with tall palm trees and misty hills, a young cartoon American soldier with a round white head, olive helmet and green uniform walking through tall grass looking nervous, and hidden among the leaves several pairs of small eyes watching him.
```

**6. Video Vietnam: caída de Saigón 1975**
```
6. A tall white apartment building rooftop at dusk with a small helicopter landing on it, a long line of cartoon people with round white heads climbing a ladder toward it, carrying small suitcases, soft purple and orange sky, city below.
```

**7. Miniatura de prueba, Irán**
```
7. YouTube thumbnail, 16:9: left side huge bold rounded cartoon text with thick black outline, "IRAN WAR" in yellow and "EXPLAINED" in white below; right side Stick (character from image 1) with a shocked face pointing at a parchment map of Iran colored dusty red with small explosion icons on it; warm tan background. Very readable at small size.
```

---

## Si la prueba sale bien
- Escribo los dos guiones completos en inglés.
- Preparo ~45–50 prompts por video en este estilo, con Stick como hilo conductor.
- Los mapas animados los hago yo con código.
