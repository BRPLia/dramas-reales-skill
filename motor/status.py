"""Fase 5: Escribe status.json final con estado del pipeline."""
import json
from pathlib import Path


def write_success(output_dir: Path, log, remotion_info: dict) -> None:
    status = {
        "status": "success",
        "phase": "complete",
        "scene": None,
        "error": None,
        "completed_assets": list(log.completed_assets),
        "elapsed_seconds": log.elapsed(),
        "output_video": remotion_info.get("output_video"),
        "remotion_project": remotion_info.get("remotion_project"),
        "composition_id": remotion_info.get("composition_id"),
        "total_frames": remotion_info.get("total_frames"),
    }
    (output_dir / "status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    log.ok(f"  status.json (success) escrito")


def write_error(output_dir: Path, log, phase: str, scene, error: str) -> None:
    status = {
        "status": "error",
        "phase": phase,
        "scene": scene,
        "error": error,
        "completed_assets": list(log.completed_assets),
        "elapsed_seconds": log.elapsed(),
        "output_video": None,
        "remotion_project": None,
    }
    (output_dir / "status.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8",
    )
    log.error(f"  status.json (error) escrito: fase={phase}, escena={scene}")
