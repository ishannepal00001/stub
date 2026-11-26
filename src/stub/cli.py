"""Command-line entry point: argument parsing and orchestration."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from . import config as config_module
from . import templates as templates_module
from . import writer
from .models import GenerationResult, RenderContext, StubError, format_stem, safe_stem
from .render import render


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stub",
        description="Create dated learning notes and language stubs.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="generate files from templates")
    generate_commands = generate.add_subparsers(dest="generate_command", required=True)
    template = generate_commands.add_parser(
        "template", help="generate a language stub from a template"
    )
    template.add_argument("language", help="template name, e.g. cpp")
    template.add_argument(
        "-l",
        "--learnings",
        action="store_true",
        help="write into the configured learnings folder and create a .md note",
    )
    template.add_argument(
        "-s",
        "--symlink",
        action="store_true",
        help="symlink the .md note into the configured vault folder (requires -l)",
    )
    template.add_argument("-n", "--name", help="filename stem; required without -l")
    template.add_argument("-m", "--message", help="extra message for the note and code")

    config = commands.add_parser("config", help="set the learnings and vault folders")
    config.add_argument("--vault", metavar="PATH", help="vault folder for .md symlinks")
    config.add_argument("--learnings", metavar="PATH", help="folder for real files")

    author = commands.add_parser("template", help="create a new template in .templates/")
    author.add_argument("language", help="new template name")
    author.add_argument("--ext", help="file extension (defaults to the language name)")
    author.add_argument("--name", help="display name stored in the template")

    return parser


def cmd_generate_template(args: argparse.Namespace) -> GenerationResult:
    if args.symlink and not args.learnings:
        raise StubError("-s requires -l; symlinks are only made for .md notes")

    paths = config_module.load_config()
    if args.symlink and paths.vault is None:
        raise StubError("no vault configured; run `stub config --vault PATH` first")

    spec = templates_module.load_template(args.language)
    note_spec = templates_module.load_markdown_template() if args.learnings else None

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    if args.learnings:
        stem = format_stem(
            spec.filename,
            date=date,
            language=args.language,
            name=safe_stem(args.name or args.language),
        )
        filename = f"{stem}.{spec.extension}"
        note_filename: str | None = (
            f"{format_stem(note_spec.filename, date=date, language=args.language, name=stem)}"
            f".{note_spec.extension}"
        )
        destination = paths.learnings
    else:
        if not args.name:
            raise StubError("-n NAME is required without -l (no .md is created in that mode)")
        stem = safe_stem(args.name)
        filename = f"{stem}.{spec.extension}"
        note_filename = None
        destination = Path.cwd()

    context = RenderContext.create(
        language=args.language,
        name=stem,
        filename=filename,
        message=args.message,
        now=now,
    )

    code_path = destination / filename
    note_path = paths.learnings / note_filename if note_filename else None
    link_path = paths.vault / note_filename if args.symlink and note_filename else None

    for path in (code_path, note_path):
        if path is not None and (path.exists() or path.is_symlink()):
            raise StubError(f"refusing to overwrite {path}")
    if link_path is not None and (link_path.exists() or link_path.is_symlink()):
        raise StubError(f"refusing to overwrite {link_path}")

    files = [writer.write_file(code_path, render(spec, context))]
    symlinks: list[Path] = []
    if note_spec is not None and note_path is not None:
        files.append(writer.write_file(note_path, render(note_spec, context)))
        if link_path is not None:
            symlinks.append(writer.link_note(link_path, note_path))

    for path in files:
        print(f"created {path}")
    for path in symlinks:
        print(f"linked {path} -> {path.resolve()}")
    return GenerationResult(files=tuple(files), symlinks=tuple(symlinks))


def cmd_config(args: argparse.Namespace) -> None:
    if args.vault is None and args.learnings is None:
        raise StubError("provide --vault and/or --learnings")
    paths = config_module.update_config(learnings=args.learnings, vault=args.vault)
    print(f"saved {config_module.config_path()}")
    print(f"learnings: {paths.learnings}")
    print(f"vault: {paths.vault or '(not set)'}")


def cmd_template(args: argparse.Namespace) -> None:
    path = templates_module.scaffold_template(args.language, args.ext, args.name)
    print(f"created template {path}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            cmd_generate_template(args)
        elif args.command == "config":
            cmd_config(args)
        elif args.command == "template":
            cmd_template(args)
    except (StubError, FileExistsError, OSError) as exc:
        print(f"stub: {exc}", file=sys.stderr)
        return 1
    return 0
