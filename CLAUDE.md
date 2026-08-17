# CLAUDE.md — Dramas-Reales Skill

Mismo contenido base que `AGENTS.md`. Para ahorrar tokens, **lee `AGENTS.md`**
(trae el onboarding y el flujo de producción) y, si necesitas el detalle del
estilo, `SKILL.md`. No hace falta leer los tres.

**Lo más importante:** mira la línea `ONBOARDING_STATUS` al inicio de `AGENTS.md`.
- `PENDIENTE` → haz el onboarding de una vez (`python generar.py doctor`,
  `python setup.py`, `python generar.py login`, `python generar.py check
  examples/guion_dramas.json`) y actualiza esa línea a `COMPLETO`.
- `COMPLETO` → no repitas onboarding; propón 3 temas al usuario, escribe el
  `guion.json` siguiendo `SKILL.md`, valida con `check` y genera.

Resumen: mini-telenovela vertical de justicia poética (~75s, 10 clips, un solo
hablante por clip, cierre con moraleja) con Google Flow + Remotion. Estilo
hardcodeado; tú solo das el `guion.json`. Video final limpio, sin marcas ni
texto. Subtítulos opcionales y locales.

⚠️ Cada corrida son 10 clips de video de pago: nunca la lances sin el OK del
usuario, y corre `python generar.py check` antes.
