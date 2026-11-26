"""Read and write config.toml at the project root."""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path

from .models import Paths, StubError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.toml"


def config_path() -> Path:
    """The config file, overridable with STUB_CONFIG."""
    override = os.environ.get("STUB_CONFIG")
    return Path(override).expanduser() if override else DEFAULT_CONFIG_PATH


def load_config(path: Path | None = None) -> Paths:
    """Load paths, falling back to ~/Learnings when no config exists."""
    path = path or config_path()
    if not path.exists():
        return Paths(learnings=Path.home() / "Learnings")
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise StubError(f"invalid config file {path}: {exc}") from exc

    section = data.get("paths", {})
    if not isinstance(section, dict):
        raise StubError(f"invalid config file {path}: [paths] must be a table")

    raw_learnings = section.get("learnings") or str(Path.home() / "Learnings")
    raw_vault = section.get("vault")
    if not isinstance(raw_learnings, str) or (raw_vault and not isinstance(raw_vault, str)):
        raise StubError(f"invalid config file {path}: paths must be strings")

    return Paths(
        learnings=Path(raw_learnings).expanduser(),
        vault=Path(raw_vault).expanduser() if raw_vault else None,
    )


def save_config(paths: Paths, path: Path | None = None) -> Path:
    """Write the fixed two-key [paths] schema. tomllib cannot write TOML."""
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["[paths]", f"learnings = {json.dumps(str(paths.learnings))}"]
    if paths.vault is not None:
        lines.append(f"vault = {json.dumps(str(paths.vault))}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def update_config(*, learnings: str | None = None, vault: str | None = None) -> Paths:
    """Change only the supplied keys and save."""
    paths = load_config()
    if learnings is not None:
        paths = Paths(learnings=Path(learnings).expanduser(), vault=paths.vault)
    if vault is not None:
        target = Path(vault).expanduser() if vault else None
        paths = Paths(learnings=paths.learnings, vault=target)
    save_config(paths)
    return paths
