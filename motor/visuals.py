"""Visuales en Google Flow: flujo HIBRIDO validado en produccion.

Mecanica por escena (dos pasos, siempre):
  Paso A — FRAME (imagen): se genera el fotograma con `media_prompt` usando
    @menciones de los personajes y del escenario. Esto congela la composicion,
    las posiciones (izquierda/derecha), la identidad y el vestuario. SIN dialogo.
  Paso B — ANIMAR (image-to-video): ese frame entra como ingrediente y el
    `motion_prompt` aporta camara + accion + el monologo hablado. El audio nativo
    (voz + SFX) viaja embebido en el mp4, asi que la voz se pega a la cara
    correcta porque las posiciones ya quedaron fijas.

Las LAMINAS (personajes y escenarios) se generan una vez, se guardan en
`recursos/<label>.png` y se suben a Flow para quedar buscables como `@label`.
Como viven en la skill, reusar el mismo label en otro guion da la misma cara y
la misma locacion: es lo que convierte varios videos en una serie.

⚠️ Los labels son GLOBALES a `recursos/`. Si dos guiones distintos declaran
`set_casa`, el segundo reusa la lamina del primero y su descripcion se ignora
en silencio. Nombra por historia: `set_casa_abuela`, no `set_casa`.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Permitir `python motor/visuals.py` (self-test) ademas de importar el paquete.
if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor import config
from motor.mentions import parse_mentions


# Lamina de PERSONAJE: cuerpo completo, fondo neutro, pose legible.
PORTRAIT_PROMPT_TEMPLATE = (
    "Full-body character reference portrait for a short drama series, vertical 9:16 format. "
    "{description} "
    "Plain neutral background, three-quarters angle facing camera, full body visible, "
    "natural relaxed pose, clear readable facial expression. "
    "No text, no lettering, no numbers, no logos anywhere in the image. "
    "Keep the exact look, wardrobe, framing and image-quality style described above fully consistent."
)

# Lamina de ESCENARIO: establishing sin personas, para anclar la locacion.
SET_PROMPT_TEMPLATE = (
    "Establishing shot of a single location for a short drama, vertical 9:16 format. "
    "EMPTY scene, absolutely NO people, no characters. "
    "{description} "
    "No readable text, no signs, no lettering, no prices, no brand labels anywhere. "
    "Wide establishing angle, clear and consistent spatial layout, props and lighting."
)


class SceneError(RuntimeError):
    def __init__(self, msg: str, scene: int):
        super().__init__(msg)
        self.scene = scene


def _load_flow_modules() -> dict:
    """Lazy-load del flow_provider validado (embebido en la skill)."""
    if str(config.BASE_DIR) not in sys.path:
        sys.path.insert(0, str(config.BASE_DIR))
    os.environ["FLOW_HEADLESS"] = "False"

    from flow_provider import settings as fs
    fs.FLOW_HEADLESS = False
    fs.FLOW_CHROME_PROFILE = config.FLOW_CHROME_PROFILE

    from flow_provider import startup, shutdown
    from flow_provider.browser import get_page
    from flow_provider.project import create_project, navigate_to_project, ensure_all_media_tab
    from flow_provider.configure import select_image_mode, select_video_mode
    from flow_provider.canvas import (
        get_canvas_count,
        capture_newest_asset_name,
        upload_standalone_image,
        select_ingredients_by_name,
    )
    from flow_provider.prompt import submit_prompt, submit_prompt_with_mentions
    from flow_provider.wait import wait_for_image, wait_for_video
    from flow_provider.download import download_latest, delete_latest_card

    return {
        "startup": startup, "shutdown": shutdown,
        "get_page": get_page,
        "create_project": create_project,
        "navigate_to_project": navigate_to_project,
        "ensure_all_media_tab": ensure_all_media_tab,
        "select_image_mode": select_image_mode,
        "select_video_mode": select_video_mode,
        "get_canvas_count": get_canvas_count,
        "capture_newest_asset_name": capture_newest_asset_name,
        "upload_standalone_image": upload_standalone_image,
        "select_ingredients_by_name": select_ingredients_by_name,
        "submit_prompt": submit_prompt,
        "submit_prompt_with_mentions": submit_prompt_with_mentions,
        "wait_for_image": wait_for_image,
        "wait_for_video": wait_for_video,
        "download_latest": download_latest,
        "delete_latest_card": delete_latest_card,
    }


def collect_sets(meta: dict, char_labels: list[str]) -> dict:
    """Escenarios a generar como {label: descripcion}, en orden de declaracion.

    `set_reference` (string) da el label `set`. `set_references` (dict) da un
    label por locacion, usado verbatim como @mencion. Pueden convivir.
    """
    sets: dict = {}
    if meta.get("set_reference"):
        sets["set"] = meta["set_reference"]
    for label, desc in (meta.get("set_references") or {}).items():
        if label in char_labels:
            raise RuntimeError(f"set_references: '{label}' choca con un label de personaje.")
        if not desc:
            raise RuntimeError(f"set_references: '{label}' sin descripcion.")
        sets[label] = desc
    return sets


def build_segments(prompt: str, sheet_map: dict) -> list[dict]:
    """Traduce @label -> el nombre con que Flow lista esa lamina en el menu @."""
    out: list[dict] = []
    for seg in parse_mentions(prompt, list(sheet_map.keys())):
        if seg["type"] == "mention":
            out.append({"type": "mention", "name": sheet_map[seg["label"]]})
        else:
            out.append(seg)
    return out


# ---------------------------------------------------------------------------
# Memoria de personajes y escenarios (recursos/personajes.json)
# ---------------------------------------------------------------------------
def registro_path() -> Path:
    return Path(config.RECURSOS_DIR) / "personajes.json"


def leer_registro() -> dict:
    """{label: {tipo, description, voice}} de todo lo que ya tiene lamina."""
    p = registro_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def registrar(tipo: str, label: str, description: str, voice: str = "") -> None:
    """Guarda la ficha junto a la lamina para reusar el personaje en otro guion."""
    reg = leer_registro()
    reg[label] = {"tipo": tipo.lower(), "description": description, "voice": voice}
    registro_path().parent.mkdir(parents=True, exist_ok=True)
    registro_path().write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")


def entidades(meta: dict) -> list[tuple[str, str, str, str]]:
    """(tipo, label, description, voice) de personajes y escenarios del guion."""
    characters = meta.get("characters", []) or []
    char_labels = [c["label"] for c in characters]
    return [
        ("Personaje", c["label"], c.get("description", ""), c.get("voice", "")) for c in characters
    ] + [
        ("Escenario", label, desc, "") for label, desc in collect_sets(meta, char_labels).items()
    ]


# ---------------------------------------------------------------------------
# Laminas (@-buscables)
# ---------------------------------------------------------------------------
async def _gen_and_download_sheet(fm, prompt: str, out_png: Path, aspect: str) -> None:
    page = await fm["get_page"]()
    await fm["ensure_all_media_tab"](page)
    await fm["select_image_mode"](model=config.IMAGE_MODEL, aspect_ratio=aspect, count=1)
    await page.wait_for_timeout(1500)
    pre = await fm["get_canvas_count"]()
    await fm["submit_prompt"](prompt)
    try:
        await fm["wait_for_image"](timeout_ms=240_000, pre_submit_count=pre)
    except Exception:
        await fm["delete_latest_card"](False)
        raise
    out_png.parent.mkdir(parents=True, exist_ok=True)
    await fm["download_latest"](output_path=str(out_png), resolution="1K", is_video=False)


async def _upload_sheet(fm, page, path: Path, aspect: str) -> None:
    await fm["select_image_mode"](model=config.IMAGE_MODEL, aspect_ratio=aspect, count=1)
    await page.wait_for_timeout(1200)
    await fm["upload_standalone_image"](str(path))


async def _prepare_sheets(guion: dict, output_dir: Path, log, fm) -> dict:
    """Asegura una lamina por personaje y por escenario. Devuelve {label: nombre @}.

    Caminos por entidad:
      1. Ya esta en sheet_map.json  -> se reusa (rerun idempotente).
      2. El PNG existe en recursos/ -> solo se sube a Flow.
      3. No existe                  -> se genera con la `description`, se guarda
                                       en recursos/ y se sube.
    """
    meta = guion["metadata"]

    map_file = output_dir / "sheet_map.json"
    sheet_map: dict = json.loads(map_file.read_text(encoding="utf-8")) if map_file.exists() else {}

    recursos = Path(config.RECURSOS_DIR)
    recursos.mkdir(parents=True, exist_ok=True)
    aspect = meta.get("aspect_ratio", config.DEFAULT_ASPECT)
    page = await fm["get_page"]()
    uploaded_any = False

    entities = entidades(meta)
    if not entities:
        log.warn("  Sin personajes ni escenarios declarados: las escenas iran sin @menciones.")
        return {}

    for tipo, label, description, voice in entities:
        if label in sheet_map:
            log.info(f"  {tipo} reanudado: {label} -> @{sheet_map[label]}")
            continue
        png = recursos / f"{label}.png"
        if not png.exists():
            if not description:
                raise RuntimeError(f"{tipo} '{label}': no hay {png.name} ni 'description' para generarlo.")
            log.info(f"  {tipo} nuevo: {label} -> generando lamina")
            template = SET_PROMPT_TEMPLATE if tipo == "Escenario" else PORTRAIT_PROMPT_TEMPLATE
            # .replace en vez de .format: las descripciones pueden traer llaves.
            await _gen_and_download_sheet(fm, template.replace("{description}", description), png, aspect)
            registrar(tipo, label, description, voice)
            log.ok(f"    Lamina guardada en {png}")
        else:
            log.info(f"  {tipo} existente: {png.name} (se reusa la lamina de recursos/)")

        log.info(f"  Subiendo {tipo.lower()}: {png.name} (buscable como @{label})")
        await page.wait_for_timeout(2500)
        await _upload_sheet(fm, page, png, aspect)
        sheet_map[label] = png.name
        map_file.write_text(json.dumps(sheet_map, indent=2, ensure_ascii=False), encoding="utf-8")
        uploaded_any = True
        log.ok(f"    {label} -> @{png.name}")

    if uploaded_any:
        log.info("    Esperando 5s y recargando para indexar en el menu @...")
        await page.wait_for_timeout(5000)
        await page.reload()
        await page.wait_for_timeout(5000)

    return sheet_map


# ---------------------------------------------------------------------------
# Escena: frame (@menciones) -> animar (I2V)
# ---------------------------------------------------------------------------
async def _gen_frame_with_mentions(fm, log, n: int, image_prompt: str, aspect: str,
                                   image_model: str, sheet_map: dict) -> str:
    page = await fm["get_page"]()
    await fm["ensure_all_media_tab"](page)
    await fm["select_image_mode"](model=image_model, aspect_ratio=aspect, count=1)
    segments = build_segments(image_prompt, sheet_map)
    pre = await fm["get_canvas_count"]()
    await fm["submit_prompt_with_mentions"](segments)
    try:
        await fm["wait_for_image"](timeout_ms=240_000, pre_submit_count=pre)
    except Exception:
        await fm["delete_latest_card"](False)
        raise
    frame_name = await fm["capture_newest_asset_name"](f"escena_{n}_frame", is_video=False)
    log.info("    Esperando 6s y recargando para indexar el frame...")
    await page.wait_for_timeout(6000)
    await page.reload()
    await page.wait_for_timeout(5000)
    return frame_name


async def _animate_frame(fm, log, n: int, motion_prompt: str, model: str, aspect: str,
                         frame_name: str, duration) -> None:
    page = await fm["get_page"]()
    await fm["ensure_all_media_tab"](page)
    await fm["select_video_mode"](
        mode="ingredientes", model=model, aspect_ratio=aspect, count=1, duration=duration,
    )
    log.info(f"    Animando el frame (I2V) con {model}: ingrediente={frame_name[:8]}...")
    await fm["select_ingredients_by_name"]([frame_name])
    await asyncio.sleep(2)
    pre = await fm["get_canvas_count"]()
    await fm["submit_prompt"](motion_prompt)
    try:
        await fm["wait_for_video"](timeout_ms=360_000, pre_submit_count=pre)
    except Exception:
        await fm["delete_latest_card"](True)
        raise


async def _download_video(fm, log, n: int, out_path: Path) -> None:
    """Descarga con reintentos SIN regenerar: regenerar cuesta creditos."""
    page = await fm["get_page"]()
    for intento in range(3):
        try:
            await fm["download_latest"](output_path=str(out_path), resolution="720p", is_video=True)
            if out_path.exists() and out_path.stat().st_size >= 100_000:
                log.ok(f"    {out_path.name} ({out_path.stat().st_size} B)")
                return
            log.warn(f"    Escena {n}: descarga {intento + 1} dio un archivo invalido, reintentando...")
        except Exception as e:
            log.warn(f"    Escena {n}: descarga {intento + 1} fallo, reintentando: {e}")
        await page.wait_for_timeout(2000)
    raise RuntimeError("Video generado pero no se pudo descargar tras 3 intentos")


async def _run_async(guion: dict, output_dir: Path, log, fm: dict) -> None:
    assets = output_dir / "assets"
    meta = guion["metadata"]
    aspect = meta.get("aspect_ratio", config.DEFAULT_ASPECT)

    await fm["startup"]()
    try:
        session_file = output_dir / "flow_session.txt"
        if session_file.exists():
            project_uuid = session_file.read_text(encoding="utf-8").strip()
            log.info(f"  Reanudando sesion Flow (Proyecto UUID: {project_uuid})")
            await fm["navigate_to_project"](project_uuid)
        else:
            project_uuid, _ = await fm["create_project"]()
            session_file.write_text(project_uuid, encoding="utf-8")
        page = await fm["get_page"]()
        log.info(f"  Enlace del Proyecto Flow: {page.url}")

        sheet_map = await _prepare_sheets(guion, output_dir, log, fm)

        for scene in guion["scenes"]:
            n = scene["scene"]
            model = scene.get("media_model", config.VIDEO_MODEL)
            image_model = scene.get("image_model", config.IMAGE_MODEL)
            duration = scene.get("duration")
            image_prompt = scene.get("media_prompt") or scene["motion_prompt"]
            motion_prompt = scene.get("motion_prompt") or scene["media_prompt"]

            out_path = assets / f"escena{n}.mp4"
            if out_path.exists() and out_path.stat().st_size >= 100_000:
                log.info(f"  Escena {n}: {out_path.name} ya existe. Saltando.")
                log.mark_asset(out_path.name)
                continue

            for intento in range(2):
                log.info(
                    f"  Escena {n} (intento {intento + 1}): HIBRIDO frame @menciones -> animar "
                    f"[{model}, dur={duration or 'default'}]"
                )
                try:
                    frame_name = await _gen_frame_with_mentions(
                        fm, log, n, image_prompt, aspect, image_model, sheet_map,
                    )
                    await _animate_frame(fm, log, n, motion_prompt, model, aspect, frame_name, duration)
                    await _download_video(fm, log, n, out_path)
                    log.mark_asset(out_path.name)
                    break
                except Exception as e:
                    if intento == 1:
                        raise SceneError(
                            f"Censura o timeout tras 2 intentos. Suaviza el prompt de esta escena: {e}", n,
                        )
                    log.warn(f"  Intento {intento + 1} fallido en la escena {n}, reintentando: {e}")

    finally:
        try:
            await fm["shutdown"]()
        except Exception as e:
            log.warn(f"shutdown Flow: {e}")


def run(guion: dict, output_dir: Path, log) -> None:
    fm = _load_flow_modules()
    asyncio.run(_run_async(guion, output_dir, log, fm))


async def _laminas_async(guion: dict, fm: dict) -> list[str]:
    """Genera SOLO las laminas que faltan (imagenes, 0 creditos de video)."""
    meta = guion["metadata"]
    aspect = meta.get("aspect_ratio", config.DEFAULT_ASPECT)
    recursos = Path(config.RECURSOS_DIR)
    faltan = [e for e in entidades(meta) if not (recursos / f"{e[1]}.png").exists()]
    if not faltan:
        return []
    await fm["startup"]()
    try:
        await fm["create_project"]()
        for tipo, label, description, voice in faltan:
            print(f"  {tipo} nuevo: {label} -> generando lamina")
            template = SET_PROMPT_TEMPLATE if tipo == "Escenario" else PORTRAIT_PROMPT_TEMPLATE
            await _gen_and_download_sheet(
                fm, template.replace("{description}", description), recursos / f"{label}.png", aspect,
            )
            registrar(tipo, label, description, voice)
    finally:
        try:
            await fm["shutdown"]()
        except Exception as e:
            print(f"shutdown Flow: {e}")
    return [e[1] for e in faltan]


def run_laminas(guion: dict) -> list[str]:
    return asyncio.run(_laminas_async(guion, _load_flow_modules()))


# ── Self-test de los helpers puros (`python motor/visuals.py`) ──────────────
if __name__ == "__main__":
    segs = build_segments(
        "Inside @set_casa, @madre on the left, @joven on the right.",
        {"madre": "madre.png", "joven": "joven.png", "set_casa": "set_casa.png"},
    )
    assert {"type": "mention", "name": "set_casa.png"} in segs
    assert {"type": "mention", "name": "madre.png"} in segs
    assert any(s["type"] == "text" and "on the left" in s["value"] for s in segs)

    assert collect_sets({"set_reference": "cocina"}, []) == {"set": "cocina"}
    assert collect_sets({"set_references": {"set_a": "A", "set_b": "B"}}, []) == {"set_a": "A", "set_b": "B"}
    assert list(collect_sets({"set_reference": "X", "set_references": {"set_b": "B"}}, [])) == ["set", "set_b"]
    assert collect_sets({}, []) == {}
    for bad in ({"set_references": {"madre": "A"}}, {"set_references": {"set_x": ""}}):
        try:
            collect_sets(bad, ["madre"])
            raise AssertionError(f"debio fallar: {bad}")
        except RuntimeError:
            pass

    # Las descripciones con llaves no deben romper la plantilla.
    tpl = PORTRAIT_PROMPT_TEMPLATE.replace("{description}", "DESC {con} llaves")
    assert "DESC {con} llaves" in tpl and "{description}" not in tpl

    print("visuals.py: OK — build_segments, collect_sets y plantillas pasaron")
