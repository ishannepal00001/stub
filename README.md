# stub

A tiny personal-learning CLI. Give it a language and it writes a dated code stub and a matching Obsidian-ready Markdown note.

> **Status:** this repository currently contains documentation only. The command-line tool described below is the specification being built next.

## What it does

`stub generate template cpp -l -s -m "Extra message"` creates:

```
/home/ishannepal/Learnings/
├── 2026-11-26_cpp.cpp
└── 2026-11-26_cpp.md
```

and adds a symlink in your configured Obsidian vault folder pointing at the `.md` file. The Markdown note records the date, time and your message; the code file carries the same information as comments.

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
| `<language>` | Template to use, e.g. `cpp`. Loads `.templates/<language>.toml`. |
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

Stores paths in `config.toml` at the project root. Each flag updates only its own key.

```
stub config --vault /home/ishannepal/Documents/Obsidian/Learnings
stub config --learnings /home/ishannepal/Learnings
```

### `stub template`

Creates a new TOML template in `.templates/`, e.g. `stub template rust --ext rs`. *(Planned alongside the main command.)*

## Configuration

`config.toml`:

```toml
[paths]
learnings = "/home/ishannepal/Learnings"
vault = "/home/ishannepal/Documents/Obsidian/Learnings"
```

`learnings` is where real files live. `vault` is the folder **inside** your Obsidian vault where `.md` symlinks are placed.

## Templates

Templates are TOML files in `.templates/`. Each language is one file, plus `markdown.toml` for the note.

`.templates/cpp.toml`:

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
│   └── writer.py
└── tests/
    ├── test_config.py
    ├── test_templates.py
    ├── test_render.py
    ├── test_writer.py
    └── test_cli.py
```

See [docs/architecture.md](docs/architecture.md) for what each module does, with examples.

## Design notes

- Python 3.11+ (uses `tomllib`); no third-party runtime dependencies.
- `pathlib` writes files exclusively (`open("x", encoding="utf-8")`), so existing work is never clobbered.
- Tests use the standard library `unittest`.

## Development

Once implemented:

```
pip install -e .
python -m unittest discover -s tests
```
