**Veredicto: SÍ CON LÍMITES.** Podemos conseguir un Short coherente y atractivo con esos tres looks. Para esta primera prueba elegiría **mapas en Python + un plano aéreo real en Blender + personajes en 2.5D**, con 7–9 planos y movimientos sencillos.

### 1. Qué resultado es viable

Los fotogramas son una referencia alcanzable de **apariencia**. La parte más exigente es mantener personajes consistentes mientras giran, manipulan objetos o caminan.

Para 48 segundos limitaría la producción a **un lugar principal, un personaje protagonista y uno o dos objetos importantes**. Así podemos dedicar tiempo al acabado.

### 2. Pipeline recomendado

| Parte | Elección para la prueba | Evaluación de tu propuesta |
|---|---|---|
| **Mapa** | Python/PIL: relieve raster + polígonos verificados + relleno translúcido + contorno luminoso. | Es la opción más sólida. Preparar el mapa con margen y resolución extra para acercamientos; aplicar las mismas transformaciones a terreno, fronteras y marcadores. |
| **Aéreo** | Un escenario sencillo en Blender, con un movimiento de cámara de 6–8 s. | Merece la pena para mostrar volumen real. Una imagen con profundidad simulada funciona para un acercamiento suave; una órbita descubre sus limitaciones. |
| **Personajes** | Un diseño maestro aprobado, separado en capas, con parpadeo, pequeños movimientos y cambios de expresión. | Mejor relación calidad/esfuerzo para un solo Short. El personaje procedural de Blender gana si después queremos producir muchos episodios. |

**Dos correcciones importantes:**

- **Natural Earth no proporciona automáticamente fronteras históricas.** Su cartografía política sigue principalmente criterios actuales de control territorial. Para 1915 o 1942 necesitamos límites de esa fecha contrastados con mapas históricos. Además, sus datos son generalizados: sirven para situar países, no para reconstruir un puerto. Sus vectores y rasters son de dominio público. [Política de fronteras](https://www.naturalearthdata.com/about/disputed-boundaries-policy/), [licencia](https://www.naturalearthdata.com/about/terms-of-use/).
- **Eevee renderiza con GPU; no tiene render por CPU.** Una integrada compatible puede servir. Si dependemos exclusivamente de CPU, la alternativa en Blender es Cycles. [Manual de Blender](https://docs.blender.org/manual/en/latest/render/eevee/limitations/limitations.html).

Para los mapas usaría primero **Natural Earth shaded relief**, por simplicidad. Blue Marble también encaja; hay que comprobar los créditos del archivo concreto y las condiciones de NASA. El relieve moderno tampoco debe introducir carreteras o ciudades actuales en una escena histórica. [Condiciones de NASA](https://www.nasa.gov/nasa-brand-center/images-and-media/).

Los iconos pueden ser PNG generados con **transparencia real**. Una familia pequeña con la misma iluminación y materiales dará más coherencia que muchos emojis distintos.

**Sobre los personajes generados:** una hoja de referencia ayuda, pero no garantiza identidad exacta entre imágenes. Reutilizar el mismo personaje recortado y editarlo conserva mejor sus rasgos. El giro amplio de cabeza y la manipulación precisa de objetos justificarían Blender.

La separación en profundidad requiere máscaras y reconstruir el fondo que queda oculto detrás del personaje. No sale automáticamente de una imagen. Vuestro [render_layers.py](</E:/Historias TIK/WarMap Stick/Scripts/render_layers.py>) ya permite posición, escala, rotación y opacidad; podemos aprovechar esa base.

**Esfuerzo orientativo, incluyendo montaje y una ronda de correcciones:**

| Alcance | Trabajo activo estimado |
|---|---:|
| Todo en 2.5D, con aspecto de render 3D | 10–18 h |
| Mezcla recomendada, incluyendo primer escenario Blender | **18–30 h** |
| Personaje propio con rig y varios escenarios en Blender | 35–60 h |

Son estimaciones de planificación, sin benchmark del equipo. Para render, mediría primero 30 fotogramas: **si tarda 2 s/fotograma, un plano de 8 s a 30 fps tarda unos 8 minutos**. Blender usaría su Python integrado, separado de vuestro Python 3.14.

### 3. Cómo hacer que parezca un solo vídeo

- **Una paleta:** mar azul oscuro, terreno verde apagado, uniformes caqui y dos colores fijos para bandos.
- **Una iluminación:** sombras suaves, luz cálida y materiales ligeramente mates tanto en iconos como en personajes.
- **Una tipografía:** subtítulos blancos con borde oscuro; amarillo para cifras. Todo el texto se añade después, sincronizado con Ryan.
- **Transiciones motivadas:** acercamiento al marcador del mapa → vista aérea del mismo lugar → detalle del personaje u objeto. Mantener orientación y dirección del movimiento.
- **Un ritmo común:** pequeños movimientos continuos y efectos sonoros compartidos, evitando cambios bruscos entre escenas estáticas y cámaras muy rápidas.

### 4. Un tema para la prueba

**Mi elección: Saint-Nazaire, 1942 — el destructor convertido en bomba para inutilizar un dique.**

Hook en inglés:

> **“Britain packed an old destroyer with explosives—and rammed it into a Nazi dock.”**

Encaja especialmente bien: mapa de la ruta, puerto geométrico fácil de simplificar y un momento humano con los comandos. El hecho central está documentado por el [National Army Museum](https://www.nam.ac.uk/explore/commandos-WW2).

Distribución visual propuesta: **0–5 s** gancho con el barco; **5–12 s** mapa; **12–21 s** aéreo del dique; **21–37 s** comandos y detalles del barco; **37–48 s** desenlace y consecuencia.

Dos alternativas:

- **Drones navales de Ucrania:** mapa → puerto → operador. Es la opción más vinculada a actualidad; hay información reciente sobre ataques presuntamente realizados con drones navales, aunque eso **no demuestra tendencia en YouTube**. [AP, 22 de noviembre de 2026](https://apnews.com/article/59f6f304f3053c69c8cc890138a94d1b).
- **Dambusters, 1943:** mapa → presa en miniatura → piloto y bomba rebotando. Muy visual, aunque avión, agua y efectos aumentan el trabajo. [RAF Museum](https://www.rafmuseum.org.uk/blog/75th-anniversary-of-the-dambusters/).

### 5. Riesgo de copiar el estilo

En términos generales, las ideas y técnicas —mapas luminosos, miniaturas, cabezas grandes— se distinguen de la expresión concreta protegida: dibujos, personajes, imágenes, guiones o música. No existe un porcentaje mágico de cambios que garantice independencia. [U.S. Copyright Office](https://www.copyright.gov/help/faq/faq-protect.html).

**Conservaría a Stick como identidad:** silueta delgada reconocible, rostro propio, proporciones definidas y chaleco PRESS cuando actúe como presentador. Los soldados llevarían uniformes de época. Cambiar únicamente casco o color al personaje de referencia sería una diferenciación débil.

Guion, recursos, composición y montaje deben ser propios. YouTube también evalúa la originalidad y el contenido reutilizado por separado del copyright. [Política de monetización](https://support.google.com/youtube/answer/1311392?hl=en).

