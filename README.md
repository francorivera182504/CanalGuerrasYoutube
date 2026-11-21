# Canal Guerras YouTube — WarMap Stick

Proyecto del canal **[@WARMAPSTICK](https://www.youtube.com/@WARMAPSTICK)**: guerras y conflictos explicados con muñequitos de palito (stickman) y mapas. Videos en inglés, producidos con IA y revisados por nosotros.

## Situación del canal (nov 2026)
- 17 suscriptores y 4 videos.
- El video ganador es **«The Russia–Ukraine War Explained in 6 Minutes (Fast Guide)»**, con más de 10 400 vistas. Sigue creciendo (~150 vistas al día) y el **89 % viene de la búsqueda de YouTube** («russia ukraine war explained», «ukraine war explained»…).
- Retención del 43 % (2:36 de 5:58).
- Países: EE. UU., India, Pakistán, Reino Unido.
- **Por qué funcionó:** responde una búsqueda que la gente hace todos los meses: «[conflicto] war explained».

## Estrategia
- **Formato base:** «[X] War Explained in 6 Minutes» para atraer tráfico de búsqueda. Se rotan otros formatos para no caer en contenido repetitivo:
  - «The 7 Levels of…»
  - «What If…»
  - «POV: You're a Soldier in…»
- **Próximos temas:**
  - **The 2026 Iran War Explained**: ~41k búsquedas al mes, +87 %.
  - **The Vietnam War Explained**: ~44k búsquedas al mes, +40 %.
- **Estilo propuesto:** dibujos de pizarra estilo «Draw My Life», con una mano que dibuja a los stickman. Mapas animados donde la frontera se traza y el territorio se pinta. Dos colores fijos para los bandos. Personaje recurrente **«Stick»**, un reportero de guerra con chaleco PRESS.
- **Meta:** empezar con 3–4 videos por semana y subir a 1 al día cuando el sistema esté pulido.
- **Monetización:** YouTube no monetiza contenido genérico o repetitivo. Cada video necesita investigación real, una historia con arco narrativo y formatos variados.

## Herramientas
| Uso | Herramienta |
|---|---|
| Guion e investigación | Claude (Claude Code) + vidIQ |
| Imágenes | Higgsfield (nano_banana_2, ~1,5 créditos por imagen) o Gemini / ChatGPT |
| Voz | edge-tts (gratis) o ElevenLabs |
| Animación y montaje | Python + ffmpeg (scripts propios) |
| Analítica | Windsor.ai (YouTube Analytics) y vidIQ |
| Títulos y miniaturas | vidIQ (puntuación) |

**Costo estimado en el estilo pizarra:** ~70 créditos de Higgsfield por video de 6 minutos. El plan Plus alcanza para ~14–17 videos al mes y el Ultra para uno diario.

## Estructura del repo
```
Guiones/                 Guiones y prompts de imágenes por video
  Estilo nuevo - PRUEBA.md
  Video 1 - Iran War/
  Video 2 - Vietnam War/
Assets/                  Recursos gráficos del canal
Miniatura/               Miniaturas
Banner.jpg, Fondo.png    Identidad del canal
```

**No están en el repo** (pesan demasiado para git): `Imagenes/` y `Audios/`, y los videos renderizados. Se comparten por Google Drive.

> Nota: los prompts de `Video 1` y `Video 2` están en el estilo antiguo (íconos en blanco y negro). Se van a rehacer con el estilo nuevo cuando aprobemos la prueba.
