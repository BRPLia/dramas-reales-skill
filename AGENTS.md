<!-- ONBOARDING_STATUS: PENDIENTE -->
# AGENTS.md — Dramas-Reales Skill 🎭

> **Agente que lee esto:** lo PRIMERO es mirar la línea `ONBOARDING_STATUS` de
> arriba. Tu comportamiento depende de ella.
>
> - `PENDIENTE` → corre el **ONBOARDING** (sección de abajo) UNA vez.
> - `COMPLETO`  → **NO repitas el onboarding.** Saluda y ve directo a
>   **PRODUCIR**: propón temas y pregunta cuál quiere.

Esta skill produce **mini-telenovelas de justicia poética** de ~75 segundos en
10 clips: alguien abusa, el abusado pone un límite, el abusador paga, y el video
cierra con una moraleja. Fotorrealista, diálogo hablado con audio nativo, video
final limpio (sin marcas, sin logos, sin texto). El estilo está **hardcodeado**;
tú solo escribes el `guion.json`. Manual completo: **[SKILL.md](./SKILL.md)**.

---

## 🚀 ONBOARDING (solo si `ONBOARDING_STATUS: PENDIENTE`)
Hazlo tú, paso a paso. Es de una sola vez. Al terminar, **actualiza este archivo**.

1. **Lee `SKILL.md`** para entender la fórmula (10 beats, regla del monólogo,
   wardrobe-lock) y los dos modos de salida (`recursos` / `video`).

2. **Verifica requisitos:** `python generar.py doctor`. Te dirá qué falta. El
   MODO `video` (video final con Remotion) necesita:
   - **Node.js 18+** y **npm** (para Remotion).
   - **FFmpeg** (con `ffprobe`) en el PATH (para medir los clips).
   - **Google Chrome** (para Flow) — lo usarás en el login.

   Si falta algo y tienes acceso a la terminal, **muestra el comando al usuario y
   pide permiso antes de ejecutarlo**:
   - Windows: `winget install OpenJS.NodeJS.LTS` y `winget install Gyan.FFmpeg`
   - macOS: `brew install node ffmpeg`
   - Linux: `sudo apt install nodejs npm ffmpeg` (o el equivalente)

   Si no puedes instalarlo, **guía al usuario** con el comando exacto. (Si solo
   quiere el MODO `recursos`, basta con Python + Chrome.)

3. **Instala dependencias:** `python setup.py`
   (pip + navegador de Playwright + `npm install` de Remotion).

4. **Login de Google (una vez):** `python generar.py login`. Se abre Chrome;
   pide al **usuario** que inicie sesión con su cuenta. Queda guardada en `session/`.

5. **Valida que todo enchufa** (gratis, no gasta créditos):
   `python generar.py check examples/guion_dramas.json`
   Debe decir `GUION OK` y listar las láminas que generaría.

6. **Pregunta al usuario si quiere correr el ejemplo completo.** Cuesta créditos
   de Flow (5 imágenes + 10 videos), así que **no lo lances sin su OK**. Si dice
   que sí: `python generar.py video examples/guion_dramas.json`.

7. **Cierra el onboarding:** edita la primera línea de ESTE archivo y cámbiala a
   `<!-- ONBOARDING_STATUS: COMPLETO (YYYY-MM-DD) -->`. Así no lo repites nunca más.

8. Dile al usuario que está listo y pasa a PRODUCIR.

---

## 🎬 PRODUCIR (cada vez que el usuario pida un video)

**Paso 1 — Elegir el tema.** Pregúntale así, con opciones para que solo tenga
que responder un número:

> ¿De qué quieres el video de hoy?
> 1. Una suegra que se cree con derecho sobre la casa de su hijo
> 2. Un jefe que se queda con el trabajo (y el mérito) de quien sí cocina
> 3. Un hermano que solo aparece cuando hay herencia que repartir
> …o dime tú el tema y lo armo.

Cambia las tres propuestas cada vez. Sácalas de los temas que rinden en
`SKILL.md`: conflicto por un **recurso** (trabajo, casa, herencia, dinero,
tiempo), sin violencia.

**Paso 2 — Escribe el guion.** Corre antes `python generar.py personajes`: si el
usuario quiere un personaje que ya existe, reúsalo con el mismo label y su ficha
copiada tal cual. Rellena primero la plantilla de 6 líneas
(abusador / víctima / recurso / creencia falsa / objeto gatillo / moraleja) y
después los 10 beats. Sigue `SKILL.md` al pie de la letra: regla del monólogo,
líneas que caben en su clip, wardrobe-lock verbatim, una sola
locación por `media_prompt`, cero `@` en los `motion_prompt`, `"silent": true` en
la escena muda.

**Paso 3 — Enséñale el guion antes de gastar créditos.** Resumen corto:
```
TÍTULO: · MODO VISUAL: · ARCO: abusador / víctima / recurso / creencia falsa / objeto gatillo / moraleja
CAST: <label>: <prenda distintiva>
GUION: los 10 beats con su hablante y su línea
```
Y pregunta: *¿Apruebas el guion? Si sí, lo valido y lanzo la generación.*

**Paso 4 — Valida gratis:** guarda el JSON (por ejemplo `mi_guion.json`) y corre
`python generar.py check mi_guion.json`. Arregla lo que marque. Te dirá también
qué láminas se **reusan** de `recursos/` y cuántos créditos vas a gastar.

**Paso 5 — Crea y enseña las láminas (gratis):**
`python generar.py laminas mi_guion.json`. Muéstrale al usuario las imágenes
nuevas de `recursos/` y espera su OK. Si una salió mal, bórrala y repite.

**Paso 6 — Genera.** Pregunta qué quiere:
- `python generar.py video mi_guion.json` → el video final ya unido.
- `python generar.py recursos mi_guion.json` → solo los clips, para su editor.

**Paso 7 — Entrega** lo de `outputs/<proyecto>/` y reporta `status.json`.

## Reglas
- **Nunca lances una generación sin el OK del usuario:** cada corrida son 10
  clips de video de pago.
- Corre `check` SIEMPRE antes de `video` o `recursos`.
- Un solo hablante por clip. Sin excepción.
- Antes de escribir el guion, mira qué hay en `recursos/`: los labels son
  globales y reusar uno te da la misma cara/locación (bueno para series, malo si
  querías otra). Nombra por historia: `set_casa_abuela`, no `set_casa`.
- Nunca afirmes muerte, asesinato o violencia física en el diálogo: el modelo lo
  censura y pierdes la corrida.
- Solo usa los comandos de `generar.py`. No inventes ni edites el motor.
- Si una escena falla dos veces, suaviza su diálogo y vuelve a correr: las
  escenas ya descargadas se saltan solas y no se pagan dos veces.
