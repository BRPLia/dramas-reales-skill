"""Logger humano con timestamps para run.log + acumulador de assets."""
import sys
import time
from pathlib import Path

# Forzar utf-8 en stdout para evitar UnicodeEncodeError en Windows (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class RunLogger:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.log_path = self.output_dir / "run.log"
        self.start_time = time.time()
        self.completed_assets: list[str] = []
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.touch()

    def _write(self, level: str, msg: str) -> None:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {level}: {msg}\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(line)
        print(line, end="")

    def info(self, msg: str) -> None: self._write("INFO", msg)
    def ok(self, msg: str) -> None: self._write("OK", msg)
    def warn(self, msg: str) -> None: self._write("WARN", msg)
    def error(self, msg: str) -> None: self._write("ERROR", msg)

    def mark_asset(self, name: str) -> None:
        if name not in self.completed_assets:
            self.completed_assets.append(name)

    def elapsed(self) -> int:
        return int(time.time() - self.start_time)
