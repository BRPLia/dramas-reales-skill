"""Subtitulos OPCIONALES, 100% locales, con faster-whisper.

Por defecto el short sale LIMPIO (sin subtitulos): el audio hablado ya viaja
dentro de cada clip de Flow. Si quieres subtitulos, pon en el guion:

    "metadata": { "subtitulos": true }

y una vez instala el extra:  pip install -r requirements-subs.txt

Esta fase extrae el audio de cada escena con ffmpeg y lo transcribe con
faster-whisper (modelo `small`, CPU, int8). No hay API, no hay cuenta, no sale
nada de tu maquina. El resultado es `assets/escenaN.json` con la forma que
consume la plantilla de Remotion:

    [{"startMs": 0, "endMs": 1400, "text": "no te queria decir nada"}, ...]

Las escenas con `"silent": true` se saltan (son mudas a proposito).
"""
import json
import subprocess
import sys
from pathlib import Path

# Permitir `python motor/subtitulos.py` (self-test) ademas de importar el paquete.
if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor import config

# Un subtitulo de drama se lee de un golpe: pocas palabras, poco tiempo.
MAX_PALABRAS = 6
MAX_SEGUNDOS = 2.5


def disponible() -> bool:
    """True si faster-whisper esta instalado (lo usa `generar.py doctor`)."""
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def _extraer_audio(mp4: Path, wav: Path) -> None:
    cmd = ["ffmpeg", "-i", str(mp4), "-vn", "-ar", "16000", "-ac", "1", "-y", str(wav)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg fallo extrayendo audio de {mp4.name}: {r.stderr[-300:]}")


def agrupar(palabras: list[dict]) -> list[dict]:
    """Agrupa palabras con timestamp en bloques cortos de subtitulo. Pura."""
    bloques: list[dict] = []
    actual: list[dict] = []

    def cerrar() -> None:
        if not actual:
            return
        bloques.append({
            "startMs": int(actual[0]["start"] * 1000),
            "endMs": int(actual[-1]["end"] * 1000),
            "text": " ".join(w["word"].strip() for w in actual).strip(),
        })
        actual.clear()

    for w in palabras:
        if not w["word"].strip():
            continue
        actual.append(w)
        largo = len(actual) >= MAX_PALABRAS
        duracion = actual[-1]["end"] - actual[0]["start"] >= MAX_SEGUNDOS
        corte = actual[-1]["word"].strip().endswith((".", "?", "!", ","))
        if largo or duracion or corte:
            cerrar()
    cerrar()
    return bloques


def run(guion: dict, output_dir: Path, log) -> None:
    assets = output_dir / "assets"
    idioma = guion["metadata"].get("language", "es")

    pendientes = [
        s for s in guion["scenes"]
        if not s.get("silent") and not (assets / f"escena{s['scene']}.json").exists()
    ]
    if not pendientes:
        log.info("  (sin escenas por transcribir)")
        return

    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError(
            "metadata.subtitulos esta en true pero falta faster-whisper. "
            "Instalalo con: pip install -r requirements-subs.txt"
        ) from e

    log.info(f"  Cargando faster-whisper ({config.WHISPER_MODEL}, CPU int8). La primera vez descarga el modelo.")
    modelo = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")

    for scene in pendientes:
        n = scene["scene"]
        mp4 = assets / f"escena{n}.mp4"
        wav = assets / f"escena{n}_asr.wav"
        destino = assets / f"escena{n}.json"

        log.info(f"  Escena {n}: extrayendo audio y transcribiendo (lang={idioma})...")
        _extraer_audio(mp4, wav)
        try:
            segmentos, _ = modelo.transcribe(str(wav), language=idioma, word_timestamps=True)
            palabras = [
                {"word": w.word, "start": w.start, "end": w.end}
                for seg in segmentos for w in (seg.words or [])
            ]
        finally:
            wav.unlink(missing_ok=True)

        bloques = agrupar(palabras)
        destino.write_text(json.dumps(bloques, indent=2, ensure_ascii=False), encoding="utf-8")
        if not bloques:
            log.warn(
                f"    escena{n}.json vacio: no se detecto habla. Si la escena es muda "
                f"a proposito, declara \"silent\": true en el guion."
            )
        else:
            log.ok(f"    escena{n}.json ({len(bloques)} subtitulos)")
        log.mark_asset(destino.name)


# ── Self-test del agrupador (`python motor/subtitulos.py`) ──────────────────
if __name__ == "__main__":
    palabras = [{"word": f"p{i}", "start": i * 0.3, "end": i * 0.3 + 0.3} for i in range(13)]
    bloques = agrupar(palabras)
    assert all(len(b["text"].split()) <= MAX_PALABRAS for b in bloques), bloques
    assert bloques[0]["startMs"] == 0
    assert bloques[-1]["endMs"] == int(12 * 0.3 * 1000 + 300)

    # Un signo de puntuacion corta el bloque antes del limite de palabras.
    cortado = agrupar([
        {"word": "hola", "start": 0.0, "end": 0.4},
        {"word": "mijo.", "start": 0.4, "end": 0.9},
        {"word": "ya", "start": 1.0, "end": 1.3},
    ])
    assert cortado[0]["text"] == "hola mijo.", cortado
    assert len(cortado) == 2, cortado

    assert agrupar([]) == []
    print("subtitulos.py: OK — agrupar paso todos los asserts")
