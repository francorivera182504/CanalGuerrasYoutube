Trabajas en `Guiones/Shorts/S11 - Bull Allen/` (WarMap Stick). Sé económico: no leas build.py entero; no toques build.py ni terrain.py.

## Tarea 1 — sound.py (editar archivo)
En `sound.py` reemplaza TODO el bloque entre la línea `EVENTS=[]` (inclúyela) y `def main():` (no incluida) por los eventos de S11. Mantén las funciones `ev(t,kind,vol,d)` y `wt(scene,word)` (wt lee timeline.json). Tipos disponibles: boom, pop, whoosh, ping, stamp, tick, brush, mg (ráfaga ametralladora, d=duración), fire. Cambia también el comentario `# ---- S10 Doss ----` por `# ---- S11 Bull Allen ----` y `music(TOTAL,92)` puede quedar.
Coreografía visual (segundos; escenas en timeline.json):
- Gancho 0–6.54: ametralladoras continuas (mg en tramos de ~0.8 s con huecos, vol .045), explosiones de mortero boom en 0.02 (vol .16), 1.5, 2.55, 4.2 (vol .12, d 1.0).
- Escena 03 (6.54–13.87): whoosh al inicio; ping suave en wt('03','July'), wt('03','New'), wt('03','Mount'); pop en wt('03','Allied') y wt('03','Japanese').
- 04: pop en wt('04','Leslie'), wt('04','stretcher-bearer'); stamp en wt('04','Bull').
- 05 (20.4–25.17): mg intermitente vol .04; boom pequeño (.08, d .7) en wt('05','Many')-.1, +.25, +.5.
- 06 (25.17–29.68): mg más denso vol .05 desde wt('06','Machine'); brush (barrido) en wt('06','sweep'); pop en wt('06','killed').
- 07 (29.68–35.09) y 08 (35.09–39.27): mg de fondo vol .04; boom (.08, d .7) en SC07+.6, wt('07','lifts')+.2, wt('07','carries'), SC08+.4, wt('08','Again'), wt('08','again'); tick (.06) cuando llega cada viaje: wt('07','carries')≈ fin de 07 (35.0), y fin de cada viaje 08 ≈ wt('08','Again')-.3, wt('08','And')-.15, 39.2.
- 09: 8 ticks (.06) en wt('09','Twelve')+.55+k*.13 (k=0..7); ping en wt('09','carried').
- 10: ping fuerte (.10) en wt('10','Silver'); whoosh en wt('10','For').
- 11: mg suave vol .035 desde 47.3 hasta el final; pop en wt('11','Would').
La voz debe quedar clara: nada por encima de .16. Luego ejecuta `python sound.py` y confirma que imprime "SFX".

## Tarea 2 — Paquete de subida
Crea `Paquete de subida (Codex).md` con: TITLE (el de guion.json + 2 alternativas ≤60 caracteres con fórmula "This [persona] + hazaña" / "The X who…"), DESCRIPTION en inglés (3 líneas, hechos de `Datos (Codex).md`, fuentes AWM / Anzac Portal, 2–3 hashtags, mencionar "Animated reconstruction. Terrain: Natural Earth, Mapzen/AWS Terrain Tiles"), TAGS (≤500 caracteres, terminando en coma), RELATED VIDEO (sugiere un largo del Pacífico del canal: "Why Did Japan Attack Pearl Harbor?"), PINNED COMMENT (pregunta), TIKTOK (texto + 5 hashtags), NOTAS (revisar a 24–48 h: ≥65 % se quedaron). Máx 250 palabras. Español salvo el copy en inglés.

Responde al final solo: "OK sonido: N eventos" y "OK paquete".
