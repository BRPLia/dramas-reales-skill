"""Ingenieria inversa de Shorts: mide videos virales para clonar su ESTRUCTURA.

    python generar.py analizar <estilo> <url> [<url> ...]

Por cada video deja en `estilos/<estilo>/evidencia/<id>/`:
  - medidas.json  duracion, cortes, tomas, transcripcion con tiempos y cifras
  - hoja.jpg      un fotograma por toma, en mosaico, para mirar el look

y en `estilos/<estilo>/resumen.json` las cifras de todos juntos.

El video descargado se BORRA al terminar: solo quedan medidas y fotogramas, que
son para estudiar el formato, no para republicar nada. Despues el agente mira la
evidencia y escribe `estilos/<estilo>/ficha.md` siguiendo `estilos/PLANTILLA.md`.

Todo es local: yt-dlp para bajar, ffmpeg para los cortes, faster-whisper (CPU)
para el texto. Sin API ni cuenta.
"""
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor import config

ESTILOS_DIR = Path(config.BASE_DIR) / "estilos"
UMBRAL_CORTE = 0.3  # sensibilidad del detector de cambio de escena de ffmpeg (0-1)


# ---------------------------------------------------------------------------
# Piezas puras (se prueban con `python motor/analisis.py`)
# ---------------------------------------------------------------------------
def tomas(cortes: list[float], duracion: float, minima: float = 0.4) -> list[tuple[float, float]]:
    """Convierte instantes de corte en tramos (inicio, fin). Ignora cortes pegados."""
    limites = [0.0]
    for c in sorted(cortes):
        if minima <= c <= duracion - minima and c - limites[-1] >= minima:
            limites.append(c)
    limites.append(duracion)
    return [(round(a, 2), round(b, 2)) for a, b in zip(limites, limites[1:])]


def cifras(duracion: float, tramos: list[tuple[float, float]], frases: list[dict]) -> dict:
    """Las medidas que importan para clonar el ritmo de un Short."""
    largos = [b - a for a, b in tramos]
    palabras = sum(len(f["texto"].split()) for f in frases)
    hablado = sum(f["fin"] - f["ini"] for f in frases)
    primera = frases[0] if frases else None
    return {
        "duracion_s": round(duracion, 1),
        "tomas": len(tramos),
        "toma_mediana_s": round(statistics.median(largos), 2) if largos else 0,
        "toma_min_s": round(min(largos), 2) if largos else 0,
        "toma_max_s": round(max(largos), 2) if largos else 0,
        "palabras": palabras,
        "palabras_por_minuto": round(palabras / duracion * 60) if duracion else 0,
        "habla_pct": round(min(hablado / duracion, 1) * 100) if duracion else 0,
        "primera_voz_s": round(primera["ini"], 2) if primera else None,
        "primeros_3s": " ".join(f["texto"] for f in frases if f["ini"] < 3).strip(),
        "frases": len(frases),
        "palabras_por_frase": round(palabras / len(frases), 1) if frases else 0,
    }


def resumir(videos: list[dict]) -> dict:
    """Mediana y rango de cada cifra numerica entre todos los videos."""
    out: dict = {"videos": len(videos)}
    if not videos:
        return out
    for k, v in videos[0]["cifras"].items():
        if not isinstance(v, (int, float)) or isinstance(v, bool):
            continue
        vals = [x["cifras"][k] for x in videos if isinstance(x["cifras"].get(k), (int, float))]
        out[k] = {"mediana": round(statistics.median(vals), 2), "min": min(vals), "max": max(vals)}
    return out


# ---------------------------------------------------------------------------
# Herramientas externas
# ---------------------------------------------------------------------------
def _ytdlp() -> list[str]:
    """El yt-dlp a usar: $YTDLP, el del PATH o el modulo de Python. YouTube cambia
    seguido: si la descarga da 403, actualiza yt-dlp (pip install -U yt-dlp)."""
    exe = os.environ.get("YTDLP") or shutil.which("yt-dlp")
    return [exe] if exe else [sys.executable, "-m", "yt_dlp"]


def _descargar(url: str, carpeta: Path) -> tuple[Path, dict]:
    js = ["--js-runtimes", "node"] if shutil.which("node") else []  # YouTube exige resolver su JS
    cmd = _ytdlp() + js + ["--no-playlist", "--no-simulate", "-j", "--quiet", "--no-warnings",
                           "-f", "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4",
                           "-o", str(carpeta / "video.%(ext)s"), url]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-300:])
    info = json.loads(r.stdout.strip().splitlines()[-1])
    mp4 = next(carpeta.glob("video.*"))
    meta = {k: info.get(k) for k in ("id", "title", "channel", "upload_date", "view_count", "like_count", "comment_count", "width", "height")}
    meta["url"] = url
    return mp4, meta


def _duracion(mp4: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def _cortes(mp4: Path) -> list[float]:
    r = subprocess.run(["ffmpeg", "-i", str(mp4), "-vf", f"select='gt(scene,{UMBRAL_CORTE})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return [float(t) for t in re.findall(r"pts_time:([\d.]+)", r.stderr)]


def _transcribir(mp4: Path, modelo) -> tuple[list[dict], str]:
    wav = mp4.with_suffix(".wav")
    subprocess.run(["ffmpeg", "-i", str(mp4), "-vn", "-ar", "16000", "-ac", "1", "-y", str(wav)],
                   capture_output=True, check=True)
    try:
        # Tiempos por palabra: sin filtro de voz, el primer segmento siempre "empieza" en 0.
        segmentos, info = modelo.transcribe(str(wav), word_timestamps=True)
        frases = [{"ini": round(s.words[0].start if s.words else s.start, 2),
                   "fin": round(s.words[-1].end if s.words else s.end, 2), "texto": s.text.strip()}
                  for s in segmentos if s.text.strip()]
    finally:
        wav.unlink(missing_ok=True)
    return frases, info.language


def _hoja(mp4: Path, tramos: list[tuple[float, float]], carpeta: Path) -> Path:
    """Un fotograma del medio de cada toma, unidos en un mosaico de 6 columnas."""
    fotos = carpeta / "fotogramas"
    fotos.mkdir(exist_ok=True)
    for i, (a, b) in enumerate(tramos, start=1):
        subprocess.run(["ffmpeg", "-ss", f"{(a + b) / 2:.2f}", "-i", str(mp4), "-frames:v", "1",
                        "-vf", "scale=-2:320", "-y", str(fotos / f"{i:03d}.jpg")], capture_output=True)
    filas = -(-len(tramos) // 6)
    hoja = carpeta / "hoja.jpg"
    subprocess.run(["ffmpeg", "-i", str(fotos / "%03d.jpg"), "-vf", f"tile=6x{filas}:padding=4", "-frames:v", "1",
                    "-y", str(hoja)], capture_output=True)
    return hoja


# ---------------------------------------------------------------------------
# Comando
# ---------------------------------------------------------------------------
def run(estilo: str, urls: list[str], conservar: bool = False) -> Path:
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise SystemExit("analizar necesita faster-whisper y yt-dlp: "
                         "pip install -r requirements-subs.txt && pip install -U yt-dlp") from e

    destino = ESTILOS_DIR / estilo
    print(f"Cargando faster-whisper ({config.WHISPER_MODEL}, CPU int8). La primera vez descarga el modelo.")
    modelo = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")

    for url in urls:
        tmp = destino / "evidencia" / "_descarga"
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        print(f"\n> {url}")
        try:
            mp4, meta = _descargar(url, tmp)
        except Exception as e:
            print(f"  NO SE PUDO BAJAR: {str(e)[:160]}")
            continue
        carpeta = destino / "evidencia" / meta["id"]
        carpeta.mkdir(parents=True, exist_ok=True)

        dur = _duracion(mp4)
        tramos = tomas(_cortes(mp4), dur)
        frases, idioma = _transcribir(mp4, modelo)
        _hoja(mp4, tramos, carpeta)
        medidas = {"video": meta, "idioma": idioma, "cifras": cifras(dur, tramos, frases),
                   "tomas": tramos, "frases": frases}
        (carpeta / "medidas.json").write_text(json.dumps(medidas, ensure_ascii=False, indent=1), encoding="utf-8")
        c = medidas["cifras"]
        print(f"  {meta['title'][:70]}")
        print(f"  {c['duracion_s']}s · {c['tomas']} tomas (mediana {c['toma_mediana_s']}s) · "
              f"{c['palabras_por_minuto']} palabras/min · primera voz {c['primera_voz_s']}s")

        if conservar:
            mp4.rename(carpeta / mp4.name)
        else:
            mp4.unlink(missing_ok=True)
        tmp.rmdir()

    videos = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(destino.glob("evidencia/*/medidas.json"))]
    resumen = resumir(videos)
    (destino / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nOK: {len(videos)} videos medidos -> {destino}")
    print("Siguiente paso: mira cada evidencia/*/hoja.jpg y medidas.json y escribe ficha.md con estilos/PLANTILLA.md")
    return destino


if __name__ == "__main__":
    t = tomas([0.1, 8.0, 8.2, 16.0, 23.9], 24.0)
    assert t == [(0.0, 8.0), (8.0, 16.0), (16.0, 24.0)], t
    f = [{"ini": 0.5, "fin": 2.5, "texto": "hola mi amor"}, {"ini": 9.0, "fin": 11.0, "texto": "te vi con ella"}]
    c = cifras(24.0, t, f)
    assert c["tomas"] == 3 and c["toma_mediana_s"] == 8.0, c
    assert c["palabras"] == 7 and c["primera_voz_s"] == 0.5 and c["primeros_3s"] == "hola mi amor", c
    assert c["habla_pct"] == 17, c
    r = resumir([{"cifras": c}, {"cifras": {**c, "tomas": 5}}])
    assert r["tomas"] == {"mediana": 4.0, "min": 3, "max": 5}, r
    assert "primeros_3s" not in r
    print("analisis.py: OK — tomas, cifras y resumir pasan los asserts")
