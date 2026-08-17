# Dramas-Reales Skill 🎭

Le das a tu agente de IA (Claude Code, Codex, Gemini, Antigravity, Cursor…) el
control para producir **mini-telenovelas de justicia poética**: alguien abusa de
otro, el abusado pone un límite, el abusador paga el precio, y el video cierra
con una moraleja. ~75 segundos en 10 clips, personajes fotorrealistas
consistentes y **diálogo hablado en español** con audio nativo.

El agente entra a **Google Flow**, crea el proyecto, genera las láminas de los
personajes y las locaciones, produce los 10 clips y **te los une en un video
final limpio** con Remotion. Sin marcas de agua, sin logos, sin texto de canal.

> Un estilo, una skill. La fórmula está **destilada y hardcodeada**: tú solo
> eliges el tema y tu agente escribe la historia.

## Instalación (la hace tu agente)

Abre tu agente de IA en una carpeta vacía y pégale esto:

> **"Clona e instala la skill de dramas-reales: https://github.com/BRPLia/dramas-reales-skill"**

El agente hará, solo:

```bash
git clone https://github.com/BRPLia/dramas-reales-skill
cd dramas-reales-skill
python setup.py            # instala dependencias + navegador (+ Remotion si hay Node)
python generar.py login    # abre Chrome -> TÚ inicias sesión -> queda guardada
python generar.py doctor   # verifica que no falte nada
```

**Requisitos:** Python 3.10+, Google Chrome, Git y una cuenta con acceso a
Google Flow. Para el modo *video* (el final ya unido) también Node 18+ y FFmpeg.
Tu agente lo verifica todo con `doctor` y te guía si falta algo.

## Cómo se usa

Le dices a tu agente *"hazme un video"* y él te pregunta el tema:

```
¿De qué quieres el video de hoy?
1. Una suegra que se cree con derecho sobre la casa de su hijo
2. Un jefe que se queda con el trabajo de quien sí cocina
3. Un hermano que solo aparece cuando hay herencia
…o dime tú el tema y lo armo.
```

Respondes `2` (o cuentas tu propia idea), el agente escribe el guion, te lo
muestra para que lo apruebes y lanza:

```bash
python generar.py check mi_guion.json      # valida GRATIS, sin gastar créditos
python generar.py video mi_guion.json      # el video final ya unido
python generar.py recursos mi_guion.json   # o solo los clips, para tu editor
```

Todo aparece en `outputs/<fecha>_<titulo>/`. Limpia con `python generar.py clean`.

> **Corre siempre `check` primero.** Cada video son 10 clips de pago en Flow: el
> validador te dice si el guion tiene errores, qué personajes se reusan y cuánto
> vas a gastar, todo sin generar nada.

## Personajes que se repiten entre videos

Las láminas de cada personaje y cada locación se guardan en `recursos/`. Si un
guion nuevo usa el mismo label (`suegra_dona`, `set_casa_abuela`), sale **la
misma cara y la misma casa**. Así es como esto se convierte en una serie con
parte 1, parte 2 y parte 3.

## Subtítulos (opcionales)

Por defecto el video sale **limpio**: el diálogo ya se escucha. Si los quieres:

```bash
pip install -r requirements-subs.txt
```
y pon `"subtitulos": true` en el `metadata` del guion. Se transcriben **en tu
propia máquina** con faster-whisper (CPU, sin API, sin cuenta, sin GPU).

## ¿Cómo escribo una buena historia?

La fórmula completa está en **[SKILL.md](./SKILL.md)**: los 10 beats, la regla
del monólogo, el diseño del villano, el wardrobe-lock, los tres modos visuales y
el safety del modelo de video. Hay un guion completo y probado en
[`examples/guion_dramas.json`](./examples/guion_dramas.json).

## Privacidad

Tu sesión de Google vive **solo en tu máquina** (`session/`, ignorada por git).
No hay API keys, no hay servidores intermedios, no se sube nada: usa tu propia
cuenta de Flow. Los subtítulos, si los activas, se generan también en local.

## Licencia

MIT — © 2026 BRPL. Úsalo, modifícalo y móntale tu propio canal.
