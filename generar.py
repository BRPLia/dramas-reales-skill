#!/usr/bin/env python
"""
generar.py — CLI de la skill DRAMAS-REALES (mini-telenovelas de justicia poetica).

Una sola puerta de entrada. El agente NO escribe codigo: solo llama a estos
comandos. El estilo esta HARDCODEADO; tu solo cambias el guion.

Comandos
--------
  python generar.py login
      Abre Chrome para iniciar sesion en Google (Flow). La sesion queda guardada
      de forma PERMANENTE en session/. Se hace una sola vez.

  python generar.py status
      Dice si ya hay sesion guardada.

  python generar.py doctor
      Verifica requisitos (Python, ffmpeg, Node, Remotion, sesion, subtitulos).

  python generar.py check <guion.json>
      Valida el guion SIN gastar un solo credito. Correlo siempre antes de
      generar: 10 clips de video cuestan caro y un typo los tira.

  python generar.py laminas <guion.json>
      Crea SOLO las laminas (personajes y escenarios) que falten. Son imagenes:
      revisalas antes de pagar los 10 clips. Quedan guardadas en recursos/.

  python generar.py personajes
      Lista los personajes y escenarios guardados con su ficha, para reusarlos
      en otro video con el mismo label.

  python generar.py recursos <guion.json>
      MODO 1 — Solo recursos. Genera y descarga los clips de cada escena
      (escena1.mp4, escena2.mp4, ...) listos para que TU los unas en tu editor.

  python generar.py video <guion.json>
      MODO 2 — Video final. Hace lo de arriba y ademas los une con Remotion en
      UN video limpio (sin marcas, sin logos, sin CTA).

  python generar.py clean [proyecto]
      Borra resultados de outputs/. Sin nombre, limpia todo.

Formato del guion: ver examples/guion_dramas.json y SKILL.md
"""
import argparse
import asyncio
import json
import re
import shutil
import sys
import traceback
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Consola UTF-8 en Windows (acentos/enes sin romper la salida).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from motor import config, status as status_mod, subtitulos, visuals, remotion_build
from motor.logger import RunLogger
from motor.mentions import mentioned_labels

FLOW_URL = "https://labs.google/fx/es-419/tools/flow"

DURACIONES_VALIDAS = {"4s", "6s", "8s", "10s"}
# "Omni Flash" = el Omni vigente (hoy 1.2). Flow retira el 5-dic-2026 Omni 1.1 y Veo Fast/Quality.
MODELOS_VIDEO = {"Omni Flash", "Omni 1.2 Flash", "Omni 1.1 Flash", "Veo 3.1 - Lite", "Veo 3.1 - Fast", "Veo 3.1 - Quality"}
# "Nano Banana 2" ya no existe en Flow: el provider selecciona la 2.1.
MODELOS_IMAGEN = {"Nano Banana 2", "Nano Banana 2.1", "Nano Banana 2 Lite", "Nano Banana Pro"}


# ---------------------------------------------------------------------------
# Utilidades de guion / salida
# ---------------------------------------------------------------------------
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")[:60] or "sin-titulo"


def validar_guion(guion: dict) -> list[str]:
    """Devuelve la lista de problemas encontrados. Vacia = guion sano. Pura."""
    problemas: list[str] = []
    if "metadata" not in guion or "scenes" not in guion:
        return ["guion invalido: faltan 'metadata' y/o 'scenes'"]

    meta = guion["metadata"]
    if not meta.get("title"):
        problemas.append("metadata.title es requerido")
    scenes = guion["scenes"]
    if not scenes:
        return problemas + ["scenes vacio"]

    char_labels = [c["label"] for c in meta.get("characters", []) or []]
    if not char_labels:
        problemas.append("metadata.characters vacio: sin personajes no hay laminas ni @menciones")
    for c in meta.get("characters", []) or []:
        if not c.get("description"):
            problemas.append(f"character '{c['label']}': falta 'description'")

    try:
        set_labels = list(visuals.collect_sets(meta, char_labels))
    except RuntimeError as e:
        problemas.append(str(e))
        set_labels = []
    if not set_labels:
        problemas.append("metadata.set_references vacio: sin escenario anclado la locacion cambia entre clips")

    todos = char_labels + set_labels
    for i, scene in enumerate(scenes, start=1):
        n = scene.get("scene")
        pre = f"escena {n}"
        if n != i:
            problemas.append(f"{pre}: las escenas deben ir numeradas 1..N en orden (esperaba {i})")
        if not scene.get("media_prompt"):
            problemas.append(f"{pre}: falta 'media_prompt' (el frame)")
        if not scene.get("motion_prompt"):
            problemas.append(f"{pre}: falta 'motion_prompt' (la animacion)")

        dur = scene.get("duration")
        if dur is not None and dur not in DURACIONES_VALIDAS:
            problemas.append(f"{pre}: duration '{dur}' invalida (usa {sorted(DURACIONES_VALIDAS)})")
        modelo = scene.get("media_model", config.VIDEO_MODEL)
        if modelo not in MODELOS_VIDEO:
            problemas.append(f"{pre}: media_model '{modelo}' desconocido (usa {sorted(MODELOS_VIDEO)})")
        if not modelo.startswith("Omni") and dur not in (None, "8s"):
            problemas.append(f"{pre}: solo los modelos Omni respetan 'duration'; {modelo} genera 8s fijos")
        img = scene.get("image_model", config.IMAGE_MODEL)
        if img not in MODELOS_IMAGEN:
            problemas.append(f"{pre}: image_model '{img}' desconocido (usa {sorted(MODELOS_IMAGEN)})")

        # Reglas duras del estilo hibrido.
        en_frame = mentioned_labels(scene.get("media_prompt") or "", todos)
        if not en_frame:
            problemas.append(f"{pre}: el media_prompt no menciona ningun @label declarado")
        sets_en_frame = [l for l in en_frame if l in set_labels]
        if len(sets_en_frame) != 1:
            problemas.append(
                f"{pre}: el media_prompt debe mencionar EXACTAMENTE una locacion @set_* "
                f"(encontradas: {sets_en_frame or 'ninguna'})"
            )
        en_motion = mentioned_labels(scene.get("motion_prompt") or "", todos)
        if en_motion:
            problemas.append(
                f"{pre}: el motion_prompt no debe llevar @menciones (duplica cuerpos). "
                f"Nombra al hablante por descriptor + posicion. Encontradas: {en_motion}"
            )

        personajes = scene.get("characters_in_scene", []) or []
        for lbl in personajes:
            if lbl not in char_labels:
                problemas.append(f"{pre}: characters_in_scene '{lbl}' no esta en metadata.characters")
        if len(personajes) > 2:
            problemas.append(f"{pre}: max 2 personajes en cuadro (hay {len(personajes)})")

        # Un solo hablante por clip: exactamente una linea hablada (o ninguna si es muda).
        lineas = _dialogos(scene)
        if scene.get("silent") is True and lineas:
            problemas.append(f"{pre}: tiene \"silent\": true pero el motion_prompt trae dialogo")
        if scene.get("silent") is not True and len(lineas) != 1:
            problemas.append(
                f"{pre}: se espera UNA linea hablada (Spanish: \"...\") y hay {len(lineas)}. "
                "Si la escena es muda, declara \"silent\": true"
            )
        if re.search(r"\[INSERT|\[TODO|<placeholder>", (scene.get("media_prompt") or "") + (scene.get("motion_prompt") or ""), re.I):
            problemas.append(f"{pre}: quedan textos de relleno sin completar")

    return problemas


def _dialogos(scene: dict) -> list[str]:
    return re.findall(r'Spanish:\s*"([^"\n]+)"', scene.get("motion_prompt") or "")


def avisos_guion(guion: dict) -> list[str]:
    """Avisos que no bloquean: ritmo de habla y duracion total. Pura."""
    avisos: list[str] = []
    total = 0
    for scene in guion["scenes"]:
        seg = int((scene.get("duration") or "8s").rstrip("s"))
        total += seg
        lineas = _dialogos(scene)
        if len(lineas) == 1 and seg > 2:
            # Grupos de vocales por segundo: aproximacion de silabas. El habla ocupa ~dur-2s.
            ritmo = len(re.findall(r"[aeiouáéíóúü]+", lineas[0].lower())) / (seg - 2)
            if ritmo > 6.2:
                avisos.append(
                    f"escena {scene.get('scene')}: la linea parece larga para {seg}s "
                    f"({len(lineas[0].split())} palabras). Recortala o sube la duracion."
                )
    if not 70 <= total <= 90:
        avisos.append(f"duracion total {total}s fuera del objetivo de 70-90s")
    return avisos


def load_guion(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        guion = json.load(f)
    problemas = validar_guion(guion)
    if problemas:
        raise ValueError("\n  - " + "\n  - ".join(problemas))
    guion["metadata"]["style"] = config.STYLE  # estilo hardcodeado
    guion["metadata"].setdefault("aspect_ratio", config.DEFAULT_ASPECT)
    guion["metadata"].setdefault("language", "es")
    return guion


def prepare_output_dir(guion: dict) -> Path:
    slug = slugify(guion["metadata"]["title"])
    out = Path(config.OUTPUT_DIR) / f"{date.today().isoformat()}_{slug}"
    (out / "assets").mkdir(parents=True, exist_ok=True)
    return out


def session_exists() -> bool:
    profile = Path(config.FLOW_CHROME_PROFILE)
    return profile.exists() and any(profile.iterdir())


# ---------------------------------------------------------------------------
# login / status / doctor / check
# ---------------------------------------------------------------------------
async def cmd_login(_args) -> int:
    from playwright.async_api import async_playwright
    from flow_provider.project import NEW_PROJECT_BUTTON

    profile = Path(config.FLOW_CHROME_PROFILE)
    profile.mkdir(parents=True, exist_ok=True)
    print("=== LOGIN GOOGLE FLOW ===")
    print(f"Perfil persistente: {profile}")
    print("Se abrira Chrome. Inicia sesion con tu cuenta de Google.")
    print("Cuando veas el boton 'Proyecto nuevo', el script guarda y cierra solo.\n")

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto(FLOW_URL)

        logged = False
        for i in range(80):  # ~240s
            await page.wait_for_timeout(3000)
            url = page.url
            try:
                ready = await page.get_by_role("button", name=NEW_PROJECT_BUTTON).count() > 0
            except Exception:
                ready = False
            if ready and "accounts.google" not in url:
                logged = True
                print("  -> Sesion detectada. Guardando...")
                await page.wait_for_timeout(3000)
                break
            if i % 5 == 0:
                print(f"  esperando login... ({url})")
        await ctx.close()

    if logged:
        print("OK: sesion guardada. Ya puedes generar videos.")
        return 0
    print("AVISO: no se detecto login. Vuelve a correr 'python generar.py login'.")
    return 1


async def cmd_status(_args) -> int:
    if session_exists():
        print(f"OK: sesion presente en {config.FLOW_CHROME_PROFILE}")
        return 0
    print("SIN SESION. Corre primero: python generar.py login")
    return 1


def cmd_doctor(_args) -> int:
    """Verifica los requisitos. Pensado para el ONBOARDING (lo corre el agente)."""
    import shutil as _sh
    print("=== DOCTOR — verificacion de requisitos ===")
    video_ready = True

    print(f"  python                 OK ({sys.version.split()[0]})")

    ffprobe = _sh.which("ffprobe")
    if ffprobe:
        print(f"  ffmpeg/ffprobe         OK ({ffprobe})")
    else:
        video_ready = False
        print("  ffmpeg/ffprobe         FALTA  -> instala FFmpeg y ponlo en el PATH (MODO video).")

    node = _sh.which("node")
    npm = _sh.which("npm")
    print(f"  node                   {'OK (' + node + ')' if node else 'FALTA  -> instala Node 18+ (MODO video).'}")
    print(f"  npm                    {'OK (' + npm + ')' if npm else 'FALTA  -> viene con Node 18+.'}")
    if not node or not npm:
        video_ready = False

    nm = Path(config.REMOTION_DIR) / "node_modules"
    print(f"  remotion/node_modules  {'OK' if nm.exists() else 'FALTA  -> corre: python setup.py'}")
    if not nm.exists():
        video_ready = False

    print(f"  sesion de Flow         {'OK' if session_exists() else 'FALTA  -> python generar.py login'}")
    print(
        f"  subtitulos (opcional)  {'OK (faster-whisper instalado)' if subtitulos.disponible() else 'no instalado -> videos sin subtitulos (por defecto). Para activarlos: pip install -r requirements-subs.txt'}"
    )

    print()
    if video_ready and session_exists():
        print("LISTO para el MODO video (video final) y el MODO recursos.")
    elif session_exists():
        print("LISTO para el MODO recursos (solo clips). Para el MODO video, resuelve lo que falta arriba.")
    else:
        print("Falta la sesion de Flow. Empieza por: python generar.py login")
    return 0


def cmd_check(args) -> int:
    path = Path(args.guion).resolve()
    try:
        with open(path, "r", encoding="utf-8") as f:
            guion = json.load(f)
    except Exception as e:
        print(f"ERROR: no se pudo leer el guion: {e}", file=sys.stderr)
        return 1

    problemas = validar_guion(guion)
    if problemas:
        print(f"GUION CON PROBLEMAS ({len(problemas)}):")
        for p in problemas:
            print(f"  - {p}")
        return 1

    meta = guion["metadata"]
    escenas = guion["scenes"]
    recursos = Path(config.RECURSOS_DIR)
    char_labels = [c["label"] for c in meta.get("characters", []) or []]
    labels = char_labels + list(visuals.collect_sets(meta, char_labels))

    print("GUION OK.")
    for a in avisos_guion(guion):
        print(f"  AVISO: {a}")
    print(f"  titulo:   {meta['title']}")
    print(f"  escenas:  {len(escenas)}")
    print(f"  subtitulos: {'si' if meta.get('subtitulos') else 'no (video limpio)'}")
    reusadas = [l for l in labels if (recursos / f"{l}.png").exists()]
    nuevas = [l for l in labels if l not in reusadas]
    if reusadas:
        print(f"  laminas que se REUSAN de recursos/: {', '.join(reusadas)}")
        print("    (si querias una cara o locacion distinta, cambia el label)")
    if nuevas:
        print(f"  laminas que se generaran ({len(nuevas)}): {', '.join(nuevas)}")
    registro = visuals.leer_registro()
    for _tipo, label, desc, _voz in visuals.entidades(meta):
        guardada = registro.get(label, {}).get("description")
        if label in reusadas and guardada and guardada != desc:
            print(f"  AVISO: '{label}' ya existe con OTRA descripcion. Se usara la lamina guardada;")
            print("         copia su ficha con 'python generar.py personajes' o cambia el label.")
    print(f"\nCosto estimado en Flow: {len(nuevas)} imagenes + {len(escenas)} videos.")
    return 0


def cmd_personajes(_args) -> int:
    """Lista los personajes y escenarios guardados, con su ficha para copiarla."""
    recursos = Path(config.RECURSOS_DIR)
    registro = visuals.leer_registro()
    laminas = sorted(p.stem for p in recursos.glob("*.png"))
    if not laminas:
        print("Aun no hay personajes guardados. Crealos con: python generar.py laminas <guion.json>")
        return 0
    print(f"PERSONAJES Y ESCENARIOS GUARDADOS ({len(laminas)}) en {recursos}")
    print("Para reusar uno en otro video: mismo label y copia su ficha tal cual.\n")
    for label in laminas:
        ficha = registro.get(label, {})
        print(f"@{label}  [{ficha.get('tipo', 'sin ficha')}]")
        if ficha.get("description"):
            print(f"  description: {ficha['description']}")
        if ficha.get("voice"):
            print(f"  voice: {ficha['voice']}")
    return 0


def cmd_laminas(args) -> int:
    """Genera solo las laminas que faltan, para revisarlas antes de pagar videos."""
    if not session_exists():
        print("SIN SESION. Corre primero: python generar.py login")
        return 1
    try:
        guion = load_guion(Path(args.guion).resolve())
    except Exception as e:
        print(f"ERROR: guion invalido: {e}", file=sys.stderr)
        return 1
    nuevas = visuals.run_laminas(guion)
    if nuevas:
        print(f"OK: laminas nuevas en recursos/: {', '.join(nuevas)}")
        print("Revisalas (ropa, cara visible, sin texto). Si una salio mal, borrala y repite.")
    else:
        print("Todas las laminas de este guion ya existian en recursos/. Nada que generar.")
    return 0


# ---------------------------------------------------------------------------
# Pipeline (modos recursos / video)
# ---------------------------------------------------------------------------
def _run_pipeline(guion_path: Path, mode: str) -> int:
    try:
        guion = load_guion(guion_path)
    except Exception as e:
        print(f"ERROR: guion invalido: {e}", file=sys.stderr)
        return 1

    output_dir = prepare_output_dir(guion)
    shutil.copy2(guion_path, output_dir / "guion.json")
    log = RunLogger(output_dir)

    log.info(f"=== INICIO dramas-reales [{mode}]: {guion['metadata']['title']} ===")

    current_phase = "init"
    try:
        current_phase = "visuals"
        log.info("FASE 1: VISUALES (Flow — frame con @menciones -> animacion I2V)")
        visuals.run(guion, output_dir, log)

        if guion["metadata"].get("subtitulos"):
            current_phase = "subtitulos"
            log.info("FASE 2: SUBTITULOS (faster-whisper local)")
            subtitulos.run(guion, output_dir, log)

        remotion_info: dict = {}
        if mode == "video":
            current_phase = "remotion"
            log.info("FASE 3: REMOTION (uniendo el video final)")
            remotion_info = remotion_build.run(guion, output_dir, log)
        else:
            current_phase = "copia"
            assets = output_dir / "assets"
            for mp4 in sorted(assets.glob("escena*.mp4")):
                shutil.copy2(mp4, output_dir / mp4.name)
            log.info("Clips copiados a la raiz del proyecto (listos para tu editor).")

        current_phase = "status"
        status_mod.write_success(output_dir, log, remotion_info)
        log.ok(f"=== EXITO ({log.elapsed()}s) -> {output_dir} ===")
        return 0

    except Exception as e:
        err_msg = f"{type(e).__name__}: {e}"
        log.error(f"FALLO en fase '{current_phase}': {err_msg}")
        log.error(traceback.format_exc().strip())
        status_mod.write_error(output_dir, log, current_phase, getattr(e, "scene", None), err_msg)
        return 1


def cmd_recursos(args) -> int:
    if not session_exists():
        print("SIN SESION. Corre primero: python generar.py login")
        return 1
    return _run_pipeline(Path(args.guion).resolve(), mode="recursos")


def cmd_video(args) -> int:
    if not session_exists():
        print("SIN SESION. Corre primero: python generar.py login")
        return 1
    return _run_pipeline(Path(args.guion).resolve(), mode="video")


def cmd_clean(args) -> int:
    out_dir = Path(config.OUTPUT_DIR)
    if args.project:
        target = out_dir / slugify(args.project)
        if not target.exists() and (out_dir / args.project).exists():
            target = out_dir / args.project
        if not target.exists():
            print(f"No existe: {target}")
            return 0
        shutil.rmtree(target)
        print(f"Borrado proyecto: {target}")
        return 0
    if not out_dir.exists():
        print(f"Nada que limpiar en {out_dir}")
        return 0
    borrados = 0
    for child in out_dir.iterdir():
        if child.name == "LEEME.txt":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        borrados += 1
    print(f"Limpiado {out_dir}: {borrados} elementos borrados.")
    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Skill DRAMAS-REALES (Google Flow + Remotion).")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("login", help="Iniciar sesion en Google Flow (una vez).")
    sub.add_parser("status", help="Ver si hay sesion guardada.")
    sub.add_parser("doctor", help="Verificar requisitos (ffmpeg, node, sesion).")

    pk = sub.add_parser("check", help="Validar el guion sin gastar creditos.")
    pk.add_argument("guion", help="Ruta al guion.json")

    sub.add_parser("personajes", help="Listar personajes y escenarios guardados.")
    pl = sub.add_parser("laminas", help="Crear solo las laminas del guion (0 creditos de video).")
    pl.add_argument("guion", help="Ruta al guion.json")

    pr = sub.add_parser("recursos", help="MODO 1: solo los clips de cada escena.")
    pr.add_argument("guion", help="Ruta al guion.json")

    pv = sub.add_parser("video", help="MODO 2: video final unido en Remotion.")
    pv.add_argument("guion", help="Ruta al guion.json")

    pc = sub.add_parser("clean", help="Borrar resultados de outputs/.")
    pc.add_argument("project", nargs="?", default=None,
                    help="Nombre/slug del proyecto. Vacio = limpiar todo.")
    return p


HANDLERS = {
    "login": cmd_login,
    "status": cmd_status,
    "doctor": cmd_doctor,
    "check": cmd_check,
    "personajes": cmd_personajes,
    "laminas": cmd_laminas,
    "recursos": cmd_recursos,
    "video": cmd_video,
    "clean": cmd_clean,
}
_ASYNC = {"login", "status"}


def main() -> int:
    args = build_parser().parse_args()
    handler = HANDLERS[args.cmd]
    if args.cmd in _ASYNC:
        return asyncio.run(handler(args))
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
