import json
from pathlib import Path

def _config_path() -> Path:
    """Ruta fija del archivo de configuración."""
    p = Path.home() / ".printervision" / "config.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def load_workspace() -> dict:
    """Carga la configuración. Si existe un archivo viejo, lo reemplaza con formato nuevo."""
    path = _config_path()
    cfg = {
        "width_mm": 480.0,
        "height_mm": 600.0,
        "last_open_dir": str(Path.home()),
        "last_save_dir": str(Path.home()),
    }

    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                old = json.load(f)
            # Si el archivo viejo no tiene las nuevas claves, se reemplaza
            if not all(k in old for k in cfg):
                save_workspace(cfg)
                return cfg
            return old
        except Exception:
            # Si hay error o formato viejo, lo reemplaza
            save_workspace(cfg)
            return cfg
    else:
        save_workspace(cfg)
        return cfg

def save_workspace(cfg: dict) -> None:
    """Guarda la configuración completa."""
    path = _config_path()
    with path.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def get_start_dir(kind: str, cfg: dict) -> Path:
    """Obtiene la carpeta inicial para abrir o guardar."""
    key = "last_open_dir" if kind == "open" else "last_save_dir"
    p = Path(cfg.get(key, str(Path.home())))
    return p if p.exists() else Path.home()

def update_last_dir(kind: str, selected_path: str | Path, cfg: dict) -> None:
    """Actualiza la última carpeta de carga o guardado y guarda el archivo."""
    p = Path(selected_path)
    folder = p if p.is_dir() else p.parent
    key = "last_open_dir" if kind == "open" else "last_save_dir"
    cfg[key] = str(folder)
    save_workspace(cfg)
