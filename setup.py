#!/usr/bin/env python
"""
setup.py — Instalacion automatica de la skill DRAMAS-REALES.

Pensado para que lo ejecute el propio agente:  python setup.py

Hace:
  1. pip install -r requirements.txt          (Playwright, Jinja2, dotenv)
  2. playwright install chromium              (navegador para Flow)
  3. npm install (dentro de remotion/)        (solo necesario para el MODO video)

El paso 3 es best-effort: si no tienes Node/npm, el MODO 'recursos' (solo clips)
funciona igual. Para el MODO 'video' (video final) si necesitas Node 18+.

Los subtitulos son OPCIONALES y no se instalan aqui. Si los quieres:
  pip install -r requirements-subs.txt

NO hace login (eso requiere TU cuenta de Google). Solo libreria estandar.
"""
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent.resolve()


def run(cmd, cwd=None) -> int:
    print(f"\n$ {' '.join(cmd)}" + (f"   (en {cwd})" if cwd else ""))
    return subprocess.call(cmd, cwd=cwd)


def main() -> int:
    print("=== Instalacion Dramas-Reales Skill ===")

    base_steps = [
        [sys.executable, "-m", "pip", "install", "-r", str(BASE / "requirements.txt")],
        [sys.executable, "-m", "playwright", "install", "chromium"],
    ]
    for cmd in base_steps:
        if run(cmd) != 0:
            print(f"\nERROR en: {' '.join(cmd)}. Revisa el mensaje de arriba.")
            return 1

    npm = shutil.which("npm")
    if npm:
        if run([npm, "install"], cwd=str(BASE / "remotion")) != 0:
            print("\nAVISO: 'npm install' fallo. El MODO 'recursos' funciona igual; "
                  "el MODO 'video' necesita Node 18+ y npm install correcto.")
    else:
        print("\nAVISO: no se encontro 'npm'. El MODO 'recursos' (solo clips) funciona.")
        print("Para el MODO 'video' (video final) instala Node 18+ y vuelve a correr setup.py.")

    print("\nOK: dependencias instaladas.")
    print("Siguiente paso (una sola vez): python generar.py login")
    print("Luego verifica todo con:        python generar.py doctor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
