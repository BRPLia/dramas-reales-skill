"""Une los clips de Flow en el video final con Remotion (modo `video`).

Self-contained: la app Remotion vive en remotion/ y tiene UNA sola composicion
(`Short`). Esta fase:
  1. Copia las escenaN.mp4 (y los escenaN.json si hay subtitulos) a remotion/assets/.
  2. Mide la duracion real de cada clip con ffprobe (nada se corta).
  3. Renderiza la plantilla del estilo a remotion/src/Main.tsx.
  4. Escribe remotion/src/meta.json (fps, tamano, duracion total).
  5. Renderiza el mp4 final y lo copia a la carpeta del proyecto.

El audio hablado ya viaja dentro de cada clip de Flow, asi que no se mezcla
ninguna pista extra. La composicion es limpia: sin marcas, sin logos, sin CTA.
"""
import json
import math
import shutil
import subprocess
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from motor import config


FPS = config.DEFAULT_FPS
COMPOSITION_ID = "Short"


def _probe_duration_frames(mp4: Path) -> int:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"ffprobe fallo en {mp4.name}: {r.stderr[-300:]}")
    return max(1, math.ceil(float(r.stdout.strip()) * FPS))


def _clean_dir(path: Path) -> None:
    if path.exists():
        for f in path.iterdir():
            if f.name == ".gitkeep":
                continue
            if f.is_dir():
                shutil.rmtree(f, ignore_errors=True)
            else:
                f.unlink()
    path.mkdir(parents=True, exist_ok=True)


def _copy_assets(src_assets: Path, dst_assets: Path, log) -> None:
    _clean_dir(dst_assets)
    for f in sorted(src_assets.iterdir()):
        if f.is_file() and f.suffix.lower() in (".mp4", ".json"):
            shutil.copy2(f, dst_assets / f.name)
    log.info(f"  Assets copiados a {dst_assets}")


def _render_main_tsx(guion: dict, log) -> int:
    style = config.STYLE
    template_path = Path(config.TEMPLATES_DIR) / f"{style}.tsx.j2"
    if not template_path.exists():
        raise FileNotFoundError(f"Plantilla no encontrada: {template_path}")

    quiere_subs = bool(guion["metadata"].get("subtitulos", False))
    assets_dir = Path(config.REMOTION_ASSETS)

    scenes_data = []
    start = 0
    for scene in guion["scenes"]:
        n = scene["scene"]
        mp4 = assets_dir / f"escena{n}.mp4"
        if not mp4.exists():
            raise FileNotFoundError(f"Falta {mp4}")
        # Las escenas mudas (o sin habla detectada) no tienen json: van sin subtitulo.
        subs_json = assets_dir / f"escena{n}.json"
        dur = _probe_duration_frames(mp4)
        scenes_data.append({
            "number": n,
            "start": start,
            "duration_frames": dur,
            "has_subs": quiere_subs and subs_json.exists(),
        })
        start += dur

    total_frames = start
    env = Environment(
        loader=FileSystemLoader(config.TEMPLATES_DIR),
        variable_start_string="<<",
        variable_end_string=">>",
        trim_blocks=False,
        lstrip_blocks=False,
        undefined=StrictUndefined,
    )
    rendered = env.get_template(f"{style}.tsx.j2").render(
        scenes=scenes_data,
        has_subs=any(s["has_subs"] for s in scenes_data),
    )

    main_tsx = Path(config.REMOTION_SRC) / "Main.tsx"
    main_tsx.parent.mkdir(parents=True, exist_ok=True)
    main_tsx.write_text(rendered, encoding="utf-8")
    log.info(f"  Main.tsx generado ({len(rendered)} B, total {total_frames} frames)")
    return total_frames


def _write_meta(total_frames: int, width: int, height: int) -> None:
    meta = {
        "compositionId": COMPOSITION_ID,
        "fps": FPS,
        "width": width,
        "height": height,
        "durationInFrames": total_frames,
    }
    (Path(config.REMOTION_SRC) / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8",
    )


def _render_video(output_mp4: Path, log) -> None:
    # Limpiar cache de Webpack — evita el crash de BatchedHash en reruns.
    webpack_cache = Path(config.REMOTION_DIR) / "node_modules" / ".cache" / "webpack"
    if webpack_cache.exists():
        shutil.rmtree(webpack_cache, ignore_errors=True)
        log.info("  Cache de Webpack limpiada")

    cmd_gpu = f'npx remotion render src/index.ts "{COMPOSITION_ID}" "{output_mp4}"'
    log.info(f"  [GPU] Renderizando: {cmd_gpu}")
    result = subprocess.run(
        cmd_gpu, cwd=config.REMOTION_DIR, shell=True,
        capture_output=True, text=True, timeout=1800,
        encoding="utf-8", errors="replace",
    )
    if result.returncode == 0:
        log.ok("  Renderizado con GPU exitoso.")
        return

    log.warn(f"  [Fallback] GPU fallo (codigo {result.returncode}). Reintentando con CPU (swangle)...")
    cmd_cpu = f'npx remotion render src/index.ts "{COMPOSITION_ID}" "{output_mp4}" --gl=swangle'
    log.info(f"  [CPU] Ejecutando: {cmd_cpu}")
    result_cpu = subprocess.run(
        cmd_cpu, cwd=config.REMOTION_DIR, shell=True,
        capture_output=True, text=True, timeout=1800,
        encoding="utf-8", errors="replace",
    )
    if result_cpu.returncode != 0:
        raise RuntimeError(
            "remotion render fallo en GPU y CPU.\n"
            f"STDOUT: {result_cpu.stdout[-500:]}\nSTDERR: {result_cpu.stderr[-500:]}"
        )


def run(guion: dict, output_dir: Path, log) -> dict:
    aspect = guion["metadata"].get("aspect_ratio", config.DEFAULT_ASPECT)
    width, height = config.DIMENSIONS.get(aspect, config.DIMENSIONS[config.DEFAULT_ASPECT])

    _copy_assets(output_dir / "assets", Path(config.REMOTION_ASSETS), log)
    total_frames = _render_main_tsx(guion, log)
    _write_meta(total_frames, width, height)
    log.info(f"  meta.json: {total_frames} frames @ {FPS}fps, {width}x{height}")

    output_mp4 = Path(config.REMOTION_DIR) / "out.mp4"
    _render_video(output_mp4, log)
    if not output_mp4.exists() or output_mp4.stat().st_size < 10_000:
        raise RuntimeError(f"Render produjo un mp4 invalido: {output_mp4}")

    final_copy = output_dir / f"{output_dir.name}.mp4"
    shutil.copy2(output_mp4, final_copy)
    output_mp4.unlink(missing_ok=True)
    log.ok(f"  Render OK ({final_copy.stat().st_size} B) -> {final_copy}")
    log.mark_asset(final_copy.name)

    return {
        "output_video": str(final_copy),
        "composition_id": COMPOSITION_ID,
        "total_frames": total_frames,
    }
