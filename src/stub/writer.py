"""File creation built around the models in models.py."""

from __future__ import annotations

from pathlib import Path

from .models import GenerationResult, Paths, StubError


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


def write_generation(
    *,
    paths: Paths,
    files: dict[Path, str],
    note_path: Path | None = None,
    symlink: bool = False,
) -> GenerationResult:
    """Write rendered files, then optionally link the note into paths.vault.

    Only models.py types are used for the inputs and result; each value in
    ``files`` is already-rendered text from render.py.
    """
    if symlink:
        if note_path is None or note_path not in files:
            raise StubError("symlink requires a generated .md note")
        if paths.vault is None:
            raise StubError("no vault configured; run `stub config --vault PATH` first")
        link = paths.vault / note_path.name
        destinations = (*files, link)
    else:
        destinations = tuple(files)

    for path in destinations:
        if path.exists() or path.is_symlink():
            raise StubError(f"refusing to overwrite {path}")

    written = tuple(write_file(path, content) for path, content in files.items())
    links: tuple[Path, ...] = ()
    if symlink and note_path is not None and paths.vault is not None:
        links = (link_note(paths.vault / note_path.name, note_path),)
    return GenerationResult(files=written, symlinks=links)
