from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def load_structured(path: str | Path) -> Any:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    raise ValueError(f"Unsupported structured file: {path}")
