"""Create files and Obsidian symlinks without overwriting existing work."""

from __future__ import annotations

from pathlib import Path


def write_file(path: Path, content: str) -> Path:
    """Write a new UTF-8 file; raise if it already exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    return path


def link_note(link: Path, target: Path) -> Path:
    """Point link at target; no-op if it already points there, else raise."""
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        if link.resolve() == target.resolve():
            return link
        raise FileExistsError(f"{link} is a symlink to a different file")
    if link.exists():
        raise FileExistsError(f"{link} already exists")
    link.symlink_to(target)
    return link
