"""Discover, load and scaffold TOML templates from source, user config or package data."""

from __future__ import annotations

import os
import shutil
import tomllib
from pathlib import Path

from .models import StubError, TemplateSpec

BUNDLED_TEMPLATES = Path(__file__).resolve().parent / "data" / "templates"


def user_templates_dir() -> Path:
    """Templates for an installed tool: ~/.config/stub/templates."""
    return Path.home() / ".config" / "stub" / "templates"


def source_templates_dir() -> Path | None:
    """Templates for a real source checkout, or None when installed as a tool."""
    root = Path(__file__).resolve().parents[2]
    if not (root / "pyproject.toml").is_file():
        return None
    return root / ".templates"


def templates_dir() -> Path:
    """The active template directory, overridable with STUB_TEMPLATES_DIR."""
    override = os.environ.get("STUB_TEMPLATES_DIR")
    if override:
        return Path(override).expanduser()
    if user_templates_dir().exists():
        return user_templates_dir()
    source = source_templates_dir()
    if source is not None and source.is_dir():
        return source
    return user_templates_dir()


def ensure_templates() -> Path:
    """Seed the active directory with bundled defaults without overwriting edits."""
    directory = templates_dir()
    directory.mkdir(parents=True, exist_ok=True)
    sources = [BUNDLED_TEMPLATES]
    source_dir = source_templates_dir()
    if source_dir is not None:
        sources.append(source_dir)
    for source in sources:
        if not source.is_dir():
            continue
        for path in source.glob("*.toml"):
            target = directory / path.name
            if not target.exists():
                shutil.copyfile(path, target)
    return directory


def load_template(language: str) -> TemplateSpec:
    """Load <language>.toml from the active directory or the bundled defaults."""
    directory = ensure_templates()
    path = directory / f"{language}.toml"
    if not path.is_file():
        bundled = BUNDLED_TEMPLATES / f"{language}.toml"
        if bundled.is_file():
            return _load(bundled)
        raise StubError(
            f"unknown template '{language}' (looked for {path}); "
            f"available: {', '.join(list_templates()) or 'none'}"
        )
    return _load(path)


def load_markdown_template() -> TemplateSpec:
    """Load the Markdown note recipe."""
    return _load(ensure_templates() / "markdown.toml")


def list_templates() -> list[str]:
    names = {path.stem for path in BUNDLED_TEMPLATES.glob("*.toml")}
    directories = [ensure_templates()]
    source_dir = source_templates_dir()
    if source_dir is not None:
        directories.append(source_dir)
    for directory in directories:
        if directory.is_dir():
            names.update(path.stem for path in directory.glob("*.toml"))
    return sorted(names)


def scaffold_template(language: str, extension: str | None = None, name: str | None = None) -> Path:
    """Create a starter TOML template in the active directory."""
    path = ensure_templates() / f"{language}.toml"
    if path.exists():
        raise StubError(f"template already exists: {path}")
    ext = (extension or language).lstrip(".")
    comment = "//" if ext in {"c", "cc", "cpp", "cxx", "h", "hpp", "java", "js", "jsx", "rs", "ts", "tsx", "go"} else "#"
    body = "\n".join(
        [
            f"{comment} ${{FILENAME}}",
            f"{comment} Date: ${{DATE}}  Time: ${{TIME}}",
            "${MESSAGE_COMMENT}" if comment == "//" else "",
            "",
        ]
    ).rstrip() + "\n"
    content = (
        f'name = "{name or language}"\n'
        f'extension = "{ext}"\n'
        'filename = "{date}_{language}"\n'
        "\n"
        "body = '''\n"
        f"{body}'''\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return path


def _load(path: Path) -> TemplateSpec:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StubError(f"template not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise StubError(f"invalid template {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise StubError(f"invalid template {path}: expected a TOML table")
    return TemplateSpec.from_mapping(data, path)
