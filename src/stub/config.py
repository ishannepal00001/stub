"""Read and write config.toml, whether stub runs from source or as a tool."""

from __future__ import annotations

import json
import os
import tomllib
from pathlib import Path

from .models import Paths, StubError


def user_config_path() -> Path:
    """Config for an installed tool: ~/.config/stub/config.toml."""
    return Path.home() / ".config" / "stub" / "config.toml"


def source_config_path() -> Path | None:
    """Config for a real source checkout, or None when installed as a tool."""
    root = Path(__file__).resolve().parents[2]
    if not (root / "pyproject.toml").is_file():
        return None
    return root / "config.toml"


def config_path() -> Path:
    """The active config file, overridable with STUB_CONFIG."""
    override = os.environ.get("STUB_CONFIG")
    if override:
        return Path(override).expanduser()
    if user_config_path().exists():
        return user_config_path()
    source = source_config_path()
    if source is not None and source.is_file():
        return source
    return user_config_path()


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
