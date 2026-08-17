"""Configuracion self-contained del motor `dramas-reales`.

Todo vive DENTRO de la skill: la sesion de Google, el Remotion embebido, las
laminas de personajes/escenarios y las salidas. Descargas la carpeta, te
logueas una vez y listo.
"""
from pathlib import Path

MOTOR_DIR = Path(__file__).parent.resolve()
BASE_DIR = MOTOR_DIR.parent.resolve()  # raiz de la skill

# Estilo hardcodeado de esta skill.
STYLE = "dramas-reales"

# Flow (Playwright) — provider validado y sesion persistente, ambos en la skill.
FLOW_PROVIDER_PATH = str(BASE_DIR / "flow_provider")
FLOW_CHROME_PROFILE = str(BASE_DIR / "session" / "flowbot-profile")

# Remotion embebido (app minima de una sola composicion).
REMOTION_DIR = str(BASE_DIR / "remotion")
REMOTION_SRC = str(BASE_DIR / "remotion" / "src")
REMOTION_ASSETS = str(BASE_DIR / "remotion" / "assets")

# Plantilla del estilo + laminas reusables + salidas.
TEMPLATES_DIR = str(MOTOR_DIR / "templates")
RECURSOS_DIR = str(BASE_DIR / "recursos")
OUTPUT_DIR = str(BASE_DIR / "outputs")

# Modelos por defecto del estilo (el guion puede sobreescribirlos por escena).
IMAGE_MODEL = "Nano Banana 2"
VIDEO_MODEL = "Omni Flash"

# Subtitulos: apagados por defecto (video limpio, audio nativo de Flow).
# Se activan con metadata.subtitulos = true y requieren requirements-subs.txt.
WHISPER_MODEL = "small"

DEFAULT_FPS = 30
DEFAULT_ASPECT = "9:16"
DIMENSIONS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:3": (1440, 1080),
    "3:4": (1080, 1440),
}
