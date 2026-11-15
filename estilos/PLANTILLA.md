# Ficha de estilo — cómo se escribe

Una ficha convierte 3–10 Shorts virales en reglas que el guion puede cumplir.
La escribe el agente **después** de `python generar.py analizar <estilo> <urls>`,
mirando `evidencia/*/hoja.jpg` (el look, toma por toma) y `evidencia/*/medidas.json`
(tiempos, cortes y transcripción) y `resumen.json` (las cifras de todos juntos).

## La regla de oro: nada sin evidencia
Cada regla de la ficha cita de dónde sale: una cifra del `resumen.json` o un
video concreto (`[id]`). Si un patrón aparece en 1 solo video, es una anécdota,
no una regla. Si los videos se contradicen, dilo.

## Qué se clona y qué no
- **Se clona la estructura:** duración, ritmo de cortes, qué pasa en los primeros
  3 segundos, cuántos personajes, cómo hablan, cómo cierra, el tipo de look.
- **No se clona el contenido:** ni sus personajes con nombre, ni sus guiones, ni
  sus frases. La historia es tuya.
- **La arquitectura de la skill no se negocia:** un solo hablante por clip,
  láminas con wardrobe-lock, cero texto en pantalla. Si el estilo original hace
  otra cosa (dos personajes hablando a la vez), la ficha anota la diferencia y
  cómo se traduce a la regla del monólogo.

## Secciones de `ficha.md`
1. **Qué es** — el formato en una frase y por qué engancha.
2. **Cifras** — tabla con mediana y rango: duración, tomas, duración de toma,
   palabras por minuto, segundo de la primera voz, palabras por frase.
3. **Los primeros 3 segundos** — qué se ve y qué se oye en cada video.
4. **El arco** — los beats que se repiten, con el segundo aproximado de cada uno.
5. **Personajes y voces** — cuántos, arquetipos, cómo se reconocen.
6. **El look** — `ancla` y `suffix` para los prompts (como los modos visuales de
   `SKILL.md`), sacados de las hojas de fotogramas.
7. **Cómo se adapta a esta skill** — qué se conserva tal cual y qué se traduce.
8. **Lo que separó a los virales de los que no** — solo si analizaste ambos.
9. **Límites** — cuántos videos, de cuándo, qué no se pudo medir.

## `ficha.json` (lo que lee `check`)
```json
{
  "estilo": "frutinovelas",
  "duracion_total_s": [90, 150],
  "escenas": [12, 18],
  "ancla": "texto que abre cada media_prompt",
  "suffix": "texto que cierra cada media_prompt y cada description"
}
```
Pon `"estilo": "<nombre>"` en el `metadata` del guion y `check` medirá contra
estas cifras en lugar de las de dramas-reales.
