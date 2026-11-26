"""Discover, load and scaffold TOML templates in .templates/."""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from .models import StubError, TemplateSpec

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEMPLATES_DIR = PROJECT_ROOT / ".templates"


def templates_dir() -> Path:
    """The template directory, overridable with STUB_TEMPLATES_DIR."""
    override = os.environ.get("STUB_TEMPLATES_DIR")
    return Path(override).expanduser() if override else DEFAULT_TEMPLATES_DIR


def load_template(language: str) -> TemplateSpec:
    """Load .templates/<language>.toml."""
    path = templates_dir() / f"{language}.toml"
    if not path.is_file():
        raise StubError(
            f"unknown template '{language}' (looked for {path}); "
            f"available: {', '.join(list_templates()) or 'none'}"
        )
    return _load(path)


def load_markdown_template() -> TemplateSpec:
    """Load the Markdown note recipe."""
    return _load(templates_dir() / "markdown.toml")


def list_templates() -> list[str]:
    directory = templates_dir()
    if not directory.is_dir():
        return []
    return sorted(path.stem for path in directory.glob("*.toml"))


def scaffold_template(language: str, extension: str | None = None, name: str | None = None) -> Path:
    """Create a starter TOML template for a new language."""
    path = templates_dir() / f"{language}.toml"
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
