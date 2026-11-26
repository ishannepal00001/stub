# stub

A tiny personal-learning CLI. Give it a language and it writes a dated code stub and a matching Obsidian-ready Markdown note.

> **Status:** implemented. Run `uv sync` and then `uv run stub --help` to get started.

## What it does

`stub generate template cpp -l -s -m "Extra message"` creates:

```
/home/ishannepal/Learnings/
├── 2026-11-26_cpp.cpp
└── 2026-11-26_cpp.md
```

and adds a symlink in your configured Obsidian vault folder pointing at the `.md` file. The Markdown note records the date, time and your message; the code file carries the same information as comments.

## Running as a CLI tool

### From the project directory (recommended)

```bash
cd /home/ishannepal/Projects/stub
uv sync
uv run stub --help
uv run stub generate template cpp -l -s -m "Extra message"
```

`uv run stub` uses the `[project.scripts]` entry in `pyproject.toml`, so no global install is needed. `uv run python -m stub` works too.

```bash
uv run stub config --vault /path/to/ObsidianVault/Learnings
uv run stub config --learnings /home/ishannepal/Learnings
uv run stub generate template cpp -n myname
uv run python -m unittest discover -s tests
```

### As a plain `stub` command from anywhere

```bash
uv tool install /home/ishannepal/Projects/stub
stub --help
stub generate template cpp -l -s -m "Extra message"
```

After changing the code, reinstall with:

```bash
cd /home/ishannepal/Projects/stub && uv tool install --reinstall .
```

Or activate the existing virtual environment manually:

```bash
source /home/ishannepal/Projects/stub/.venv/bin/activate
stub --help
```

For an installed tool, paths live in `~/.config/stub/config.toml` and templates in `~/.config/stub/templates/`. When running from the source checkout, the project's `config.toml` and `.templates/` are used instead. Override either with `STUB_CONFIG` and `STUB_TEMPLATES_DIR`.

## Commands

```
stub generate template <language> [-l] [-s] [-n NAME] [-m "MSG"]
stub config --vault <path> [--learnings <path>]
stub config --learnings <path> [--vault <path>]
stub template <language> [--ext EXT] [--name NAME]
stub --help
```

Every level has `--help` (`stub generate --help`, `stub config --help`, etc.).

### `stub generate template`

| Flag | Meaning |
| --- | --- |
| `<language>` | Template to use, e.g. `cpp`. Loads `<language>.toml` from the active template directory. |
| `-l` | Write the generated pair into the configured learnings folder instead of the current directory. Enables Markdown output. |
| `-s` | Also symlink the generated `.md` into the configured vault folder. Requires `-l`. |
| `-n NAME` | Filename to use **when `-l` is not passed**. Required in that case. |
| `-m "MSG"` | Extra message. Rendered as `_MSG_` in Markdown and `// MSG` in code. Omitted when not given. |

Behaviour:

| Invocation | Result |
| --- | --- |
| `stub generate template cpp -l -s -m "Extra message"` | Dated `.cpp` + `.md` in `Learnings/`, `.md` symlinked into the vault |
| `stub generate template cpp -l` | Dated `.cpp` + `.md` in `Learnings/`, no symlink |
| `stub generate template cpp -n myname -m "Extra message"` | `./myname.cpp` only — no `.md`, no symlink |
| `-s` without `-l`, or no vault configured | Clear error; no partial files written |

With `-l`, filenames are `<YYYY-MM-DD>_<language>.<extension>`, for example `2026-11-26_cpp.cpp` and `2026-11-26_cpp.md`. Without `-l`, the file is `<NAME>.<extension>` in the current directory.

Existing files are never overwritten.

### `stub config`

Stores paths in `~/.config/stub/config.toml` when installed as a tool, or the project's `config.toml` when running from source. Each flag updates only its own key.

```
stub config --vault /home/ishannepal/Documents/Obsidian/Learnings
stub config --learnings /home/ishannepal/Learnings
```

### `stub template`

Creates a new TOML template in the active template directory, e.g. `stub template rust --ext rs`. For an installed tool that is `~/.config/stub/templates/`; for a source checkout it is `.templates/`.

## Configuration

The active config is `~/.config/stub/config.toml` for an installed tool, or `config.toml` at the project root when running from source. Set `STUB_CONFIG` to use a different file.

```toml
[paths]
learnings = "/home/ishannepal/Learnings"
vault = "/home/ishannepal/Documents/Obsidian/Learnings"
```

Set the vault after installing with `stub config --vault /path/to/ObsidianVault/Learnings`. Without it, `-s` reports an error. `learnings` is where real files live; `vault` is the folder **inside** your Obsidian vault where `.md` symlinks are placed.

## Templates

Bundled defaults ship in `src/stub/data/templates/`. On first use they are copied into the active template directory — `~/.config/stub/templates/` for an installed tool, or the project's `.templates/` when running from source. Existing templates are never overwritten, so your edits survive reinstalls. Set `STUB_TEMPLATES_DIR` to use another directory.

Example `.templates/cpp.toml` (same format in every location):

```toml
name = "cpp"
extension = "cpp"
filename = "{date}_{language}"

body = '''
// ${FILENAME}
// Date: ${DATE}  Time: ${TIME}
${MESSAGE_COMMENT}

#include <iostream>

int main() {
    return 0;
}
'''
```

`.templates/markdown.toml`:

```toml
name = "markdown"
extension = "md"
filename = "{date}_{language}"

body = '''
# ${TITLE}

- Date: ${DATE}
- Time: ${TIME}
- Language: ${LANGUAGE}

${MESSAGE_MD}
'''
```

Bodies use TOML literal strings (`'''...'''`) so C++ braces and backslashes are preserved exactly.

### Placeholders

| Placeholder | Value |
| --- | --- |
| `${DATE}` | `2026-11-26` |
| `${TIME}` | `14:32:07` |
| `${TIMESTAMP}` | ISO date + time |
| `${LANGUAGE}` | `cpp` |
| `${NAME}` | Custom name from `-n`, or the generated stem |
| `${FILENAME}` | Full generated filename |
| `${TITLE}` | Human-readable title, e.g. `2026-11-26 cpp` |
| `${MESSAGE_MD}` | `_Extra message_` — empty when no `-m` |
| `${MESSAGE_COMMENT}` | `// Extra message` — empty when no `-m` |

Lines that become empty after substitution are removed, so omitting `-m` leaves no stray `_ _` or `//`.

Substitution uses `string.Template`, not `str.format()` — the braces in `int main() {` must survive unchanged.

## Obsidian symlinks

The real note stays in `Learnings/`; the vault holds a symlink to it. Obsidian on desktop indexes symlinked Markdown files and writes edits straight through to the real file.

Caveats:

- Obsidian Sync does not sync targets outside the vault.
- Obsidian Mobile does not support symlinks.
- Obsidian may need a reindex if a symlink appears while it is running.

If those matter, set the vault folder as the learnings folder and skip `-s`.

## Project structure

```
stub/
├── pyproject.toml
├── README.md
├── docs/
│   └── architecture.md
├── config.toml
├── .templates/
│   ├── cpp.toml
│   └── markdown.toml
├── src/stub/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── templates.py
│   ├── models.py
│   ├── render.py
│   ├── writer.py
│   └── data/templates/        # bundled defaults, copied on first use
│       ├── cpp.toml
│       └── markdown.toml
└── tests/
    ├── test_config.py
    ├── test_templates.py
    ├── test_models.py
    ├── test_render.py
    ├── test_writer.py
    └── test_cli.py
```

See [docs/architecture.md](docs/architecture.md) for what each module does, with examples.

## Design notes

- Python 3.11+ (uses `tomllib`). Dependencies are managed with `uv` and pinned in `uv.lock`.
- `models.py` uses frozen **pydantic v2** models (`Paths`, `TemplateSpec`, `RenderContext`, `GenerationResult`); everything else stays stdlib-only.
- `pathlib` writes files exclusively (`open("x", encoding="utf-8")`), so existing work is never clobbered.
- Tests use the standard library `unittest`.

## Development

```
uv sync
uv run stub --help
uv run python -m unittest discover -s tests
```
