"""Parser de menciones @label para el menu inline de Google Flow.

El guion escribe los prompts de IMAGEN con los personajes y escenarios
referenciados por @:

    "Inside @set_casa, @madre stands on the left, @joven on the right."

Este modulo NO toca el navegador. Solo convierte ese string en una secuencia
ordenada de segmentos de texto y menciones, que el provider luego reproduce en
Flow (escribir texto + abrir menu @ + seleccionar el recurso).

Reglas:
- Solo se reconoce como mencion un "@" seguido de un label DEFINIDO (personaje
  o escenario). Un "@" suelto (ej. un email) se deja como texto literal.
- Ante labels que comparten prefijo (ej. "ma" y "mama"), gana el MAS LARGO.
"""
import re


def parse_mentions(prompt: str, labels: list[str]) -> list[dict]:
    """Divide `prompt` en segmentos {"type": "text"|"mention"}."""
    if not labels:
        return [{"type": "text", "value": prompt}] if prompt else []

    ordered = sorted({l for l in labels if l}, key=len, reverse=True)
    alt = "|".join(re.escape(l) for l in ordered)
    # (?<![\w@]) evita @ pegado a una palabra previa (ej. correo).
    # (?![\w]) asegura que el label termina donde debe.
    pattern = re.compile(rf"(?<![\w@])@({alt})(?![\w])")

    segments: list[dict] = []
    pos = 0
    for m in pattern.finditer(prompt):
        if m.start() > pos:
            segments.append({"type": "text", "value": prompt[pos:m.start()]})
        segments.append({"type": "mention", "label": m.group(1)})
        pos = m.end()
    if pos < len(prompt):
        segments.append({"type": "text", "value": prompt[pos:]})
    return segments


def mentioned_labels(prompt: str, labels: list[str]) -> list[str]:
    """Labels presentes en el prompt, en orden de aparicion, sin repetir."""
    seen: list[str] = []
    for seg in parse_mentions(prompt, labels):
        if seg["type"] == "mention" and seg["label"] not in seen:
            seen.append(seg["label"])
    return seen


# ── Self-test (`python motor/mentions.py`) ──────────────────────────────────
if __name__ == "__main__":
    labels = ["madre", "joven", "set_casa", "ma"]

    out = parse_mentions("Inside @set_casa, @madre on the left, @joven on the right.", labels)
    assert out[0] == {"type": "text", "value": "Inside "}
    assert {"type": "mention", "label": "set_casa"} in out
    assert {"type": "mention", "label": "madre"} in out
    assert {"type": "mention", "label": "joven"} in out

    # El label mas largo gana sobre el corto.
    assert parse_mentions("@madre llega", labels)[0] == {"type": "mention", "label": "madre"}

    # Un @ que no es label se queda como texto.
    assert parse_mentions("escribe a juan@correo.com", labels) == [
        {"type": "text", "value": "escribe a juan@correo.com"}
    ]

    assert mentioned_labels("@joven habla, @madre calla, @joven insiste", labels) == ["joven", "madre"]

    print("mentions.py: OK — todos los asserts pasaron")
