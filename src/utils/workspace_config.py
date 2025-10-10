import json
from pathlib import Path

_DEF = {"width_mm": 480.0, "height_mm": 600.0}

def _default_path() -> Path:
    p = Path.home() / ".printervision" / "config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def load_workspace(path: Path | None = None) -> dict:
    path = path or _default_path()
    if not path.exists():
        save_workspace(_DEF, path)
        return _DEF.copy()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # mínimos seguros
    w = float(data.get("width_mm", _DEF["width_mm"]))
    h = float(data.get("height_mm", _DEF["height_mm"]))
    return {"width_mm": w, "height_mm": h}

def save_workspace(ws: dict, path: Path | None = None) -> None:
    path = path or _default_path()
    data = {
        "width_mm": float(ws.get("width_mm", _DEF["width_mm"])),
        "height_mm": float(ws.get("height_mm", _DEF["height_mm"])),
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)