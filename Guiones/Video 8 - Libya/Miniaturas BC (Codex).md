# Miniaturas B y C — Video 8: Libya

## Análisis del Video 7 (6 líneas)

1. Las 54 visitas son el dato facilitado por Franco: sin impresiones ni CTR por fuente, el fallo de clics es una hipótesis, no una conclusión demostrada.
2. El paquete de subida recomienda A → C → B del primer juego; no registra cuál se publicó ni confirma el uso de v2. Revisé ambos juegos y sus hojas comparativas.
3. «HOW IT CONNECTS» y «WHY NO PEACE?» son legibles pero abstractos; «78 YEARS OF CONFLICT» promete un resumen amplio y «HOW IT BEGAN» no concreta el misterio.
4. Mapas, varios personajes, flechas, explosiones y texto reparten la atención: a 160 px desaparecen fronteras, civiles y gestos pequeños, aunque sobreviven los titulares.
5. El amarillo/blanco sobre oscuro funciona; en v2, el rojo de mapas y trayectorias compite con las caras, y tres expresiones serias transmiten menos emoción que una única reacción grande.
6. Rescato el antes/después de `v2_B_1948_2026_split.png`: su contraste temporal se entiende rápido; B lo adapta al mismo barco, elimina mapas, fechas, familia y cara superpuesta, y reduce el texto a «SAFE?».

## B — SAFE?

Adaptación concreta del contraste antes/después del Video 7: la Merkury 734 erguida frente a la misma corbeta volcada. Cian claro frente a azul oscuro; dos estados del mismo sujeto y una pregunta de una palabra. El misterio es por qué el puerto no la protegió. El número 734 identifica el casco, no una cifra de pérdidas. Reconstrucción conceptual en Bengasi, sin afirmar que sean imágenes reales del momento.

## C — WHY HERE?

Dirección distinta: reacción emocional de un comandante ruso genérico, cabeza blanca redonda, boca abierta y cejas de alarma. El personaje domina aproximadamente el 55–60 % del ancho del cuadro, ocupa toda su altura y es el foco principal; el barco volcado es solo una pista secundaria. Tres elementos: personaje, titular de dos palabras y silueta naval. Fondo rojo, cara blanca y texto amarillo. La pregunta exige la explicación del video sobre Libia; no inventa una próxima víctima ni reproduce una declaración real.

## Prompts finales

Herramienta utilizada: generación integrada de imágenes (`image_gen`), una generación por variante. Referencias locales para estilo/composición; reducción técnica posterior a 1280 × 720 con Lanczos y optimización PNG, sin repintado por código.

### B

```text
Use case: ads-marketing.
Create ONE finished original YouTube thumbnail for WarMap Stick, landscape 16:9, 1280x720 PNG.
Input images are STYLE AND MECHANISM REFERENCES ONLY: image 1 Middle East contact sheet shows a before/after visual contrast; image 2 Libya thumbnail shows thick ink outlines and cartoon ship design. Do not reproduce contact sheet, labels or its maps.
Primary request: adapt the before/after split mechanism from the Middle East 1948/2026 thumbnail to the SAME Russian corvette Merkury, hull number 734, at Benghazi. Large clear ship forms, brutally simple composition: left 42% warm pale sand/cyan, ship upright; right 58% dark navy water, SAME ship CAPSIZED ON ITS SIDE, hull rolled 90 degrees, superstructure sideways touching water, broad hull exposed. This must read as a capsized corvette, not an intact ship with a broken bow. The left and right represent before/after, not two destroyed ships.
Both depictions are close cropped to fill the bottom 65% of each half, silhouette immediately recognizable. A single irregular diagonal black division, no graphic boxes or grid. No people, drone, explosion, smoke, maps, arrows or secondary objects. A thin sandy quay strip may establish a harbour but no detailed buildings.
Text verbatim: "SAFE?" in an ENORMOUS condensed heavy sans serif across top, yellow with thick black outline, at least 210px cap height, simple horizontal letters, ample margins.
Style: vivid flat hand drawn cartoon, very thick black contours, clean shapes, NO photorealism, NO realistic rendering or textures. Navy, bright cyan, sand, yellow and grey. White hull number "734" on the upright ship only, no other small text. No dates, figures, corner tags, capsules, captions or watermark.
Payoff: apparent harbour security versus the actual capsizing; do not claim loss of Africa or another vessel. Strong legibility at 160 pixels.
```

### C

```text
Use case: ads-marketing.
Create ONE finished original YouTube thumbnail for WarMap Stick, 16:9 landscape 1280x720 PNG. Style reference is only the round white stickman face, bold black contour and flat cartoon colours in the referenced Middle East sheet. Do not copy its composition, maps, multiple panels or other text.
Concept C: a Russian naval commander's sudden alarm that the war has reached Libya, with an unresolved WHY. EXACTLY three visual elements: one enormous expressive stickman bust, the headline, one small capsized grey corvette silhouette. A single huge white perfectly ROUND stickman head with very thick black outline and thin black stick arms, simple dark navy naval jacket with a small plain Russian tricolour patch integrated in it. No realistic skin or portrait, no elaborate hat, no fingers. Face is the overwhelming focus, occupies at least 55% of the entire frame area, on right and centre, cropped bust with head fully within frame. Raised asymmetrical eyebrows, huge worried black oval eyes, clearly open mouth of shock, one simple sweat drop. His eyes look toward the tiny ship on lower left. Expressive, readable at 160px.
Headline EXACTLY "WHY HERE?" in two lines at upper left, gigantic bold condensed sans serif capitals, warm yellow with thick black contour, horizontal and straight, at least 160 px letter height per line, completely legible with generous margins. No quotes or other headline.
Lower left, one simple grey Russian corvette CAPSIZED ON ITS SIDE, recognizable rolled hull and sideways superstructure in a plain narrow cyan water band; it is a secondary cue only, no explosion, drone, fire or smoke. No extra small text or numbers. This is an illustrative reaction, not a claimed real photographed expression.
Background is solid deep red/burgundy, FLAT vivid colours throughout, clean bold black ink outlines, no gradients, glow, textures, photorealism or 3D rendering. No map, arrows, grid, split screen, capsules, labels, corner tags, logos, watermark, extra characters or objects. Avoid top/bottom text cropping. Keep lower right quiet for YouTube duration overlay.
```

## Revisión visual y técnica

- Inspección visual de las dos generaciones y de la hoja final a 640 × 360, 320 × 180 y 160 × 90.
- «SAFE?» y «WHY HERE?» están bien escritos, completos y legibles a 160 px. A esa escala se conserva la diferencia entre barco erguido y volcado en B, y la emoción de la cara en C; los detalles del barco secundario de C se simplifican.
- B muestra la corbeta sobre un costado, con casco expuesto y superestructura lateral en el agua. C usa una silueta simplificada del vuelco, sin representar la Angara hundida.
- Sin mapas en B/C, sin cuadrícula, cápsulas, etiquetas de esquina ni fotorrealismo. No fue necesaria otra generación tras revisar texto y legibilidad.
- `Miniatura/Libya/02_B.png`: 1280 × 720, 890.533 bytes.
- `Miniatura/Libya/03_C.png`: 1280 × 720, 679.367 bytes.
- `Miniatura/Libya/_sheet_bc.jpg`: A/B/C lado a lado, con filas adicionales de 320 × 180 y 160 × 90.
- A y los archivos antiguos permanecen intactos; en Test & Compare, seleccionar 01_Libya.png, 02_B.png y 03_C.png. No se cambió la prueba en YouTube.
- Son hipótesis creativas para probar con el mismo título; no hay puntuación predictiva de vidIQ ni garantía de CTR.

