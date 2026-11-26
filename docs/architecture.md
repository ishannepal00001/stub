# Architecture

This document explains the roles of each module in plain language, with examples.

## The short version

```
you → cli.py → config.py  (WHERE do files go?)
             → templates.py (WHAT do I write?)
             → render.py    (FILL IN the blanks)
             → writer.py    (SAVE + LINK)
```

Each module has one job. It passes its result to the next module and never does the next module's work.

## Module roles

### `cli.py` — the receptionist

Reads what you typed and turns it into a plain description of the job. It does not write files itself.

```
stub generate template cpp -l -s -m "Extra message"
```

becomes roughly:

```python
{
    "language": "cpp",
    "learnings": True,
    "symlink": True,
    "message": "Extra message",
    "name": None,
}
```

It also enforces the rules: `-s` needs `-l`; without `-l`, `-n NAME` is required.

### `config.py` — the address book

Only knows paths. It reads `config.toml` and changes one key when you run `stub config`.

```
stub config --vault /home/ishannepal/Documents/Obsidian/Learnings
```

changes only the `vault` line and leaves `learnings` alone.

### `templates.py` — the recipe drawer

Given a language name, it finds the matching recipe in `.templates/` and returns its extension and body text. It never fills in the recipe.

```
cpp → .templates/cpp.toml → extension = "cpp", body = '''...'''
```

It also handles `stub template cpp --ext cpp` when you want to create a new recipe.

### `models.py` — the labelled boxes

Small frozen pydantic models that carry values between modules so no module has to guess another's format.

```python
RenderContext(
    date="2026-11-26",
    time="14:32:07",
    language="cpp",
    message="Extra message",
)
```

### `render.py` — fill in the blanks

Takes a recipe containing `${...}` blanks plus a context of values, and returns finished text. It also shapes the message for each output type.

```
${MESSAGE_COMMENT} → // Extra message
${MESSAGE_MD}      → _Extra message_
${DATE}            → 2026-11-26
```

It uses `string.Template.safe_substitute()`, so the `{` in `int main() {` is left alone. `str.format()` would treat it as a placeholder and fail.

### `writer.py` — the hands

Creates folders and files for real. Uses exclusive creation so an existing file is never silently overwritten, then adds the Obsidian symlink if asked.

```
/home/ishannepal/Learnings/2026-11-26_cpp.cpp    ← new file
/home/ishannepal/Learnings/2026-11-26_cpp.md     ← new file
/home/ishannepal/Vault/Learnings/2026-11-26_cpp.md
    → /home/ishannepal/Learnings/2026-11-26_cpp.md   ← symlink
```

## One full walkthrough

Command:

```
stub generate template cpp -l -s -m "Extra message"
```

1. **cli** parses the flags and checks that `-s` comes with `-l`.
2. **config** reports `learnings = /home/ishannepal/Learnings` and `vault = .../Vault/Learnings`.
3. **templates** loads `cpp.toml` and `markdown.toml`.
4. **render** builds the context and fills both recipes.
5. **writer** writes both files into `Learnings/`, then creates the symlink in the vault.

Result — `2026-11-26_cpp.cpp`:

```cpp
// 2026-11-26_cpp.cpp
// Date: 2026-11-26  Time: 14:32:07
// Extra message

#include <iostream>

int main() {
    return 0;
}
```

Result — `2026-11-26_cpp.md`:

```md
# 2026-11-26 cpp

- Date: 2026-11-26
- Time: 14:32:07
- Language: cpp

_Extra message_
```

## Contrast: no `-l`

```
stub generate template cpp -n myname -m "Extra message"
```

The first four steps are the same, except:

- **cli** requires `-n` because `-l` is absent.
- **templates** loads only `cpp.toml` — there is no Markdown recipe in this mode.
- **writer** writes `./myname.cpp` in the current directory and creates no symlink.

## Why split it up

| Change you want to make | File you touch |
| --- | --- |
| Different comment text in generated C++ | `.templates/cpp.toml` |
| Move the learnings or vault folder | `config.toml` |
| Copy files instead of symlinking | `src/stub/writer.py` |
| Add a new flag | `src/stub/cli.py` |
| Add a new placeholder | `src/stub/render.py` |

Each module also has a matching test file under `tests/`, so a change can be checked in isolation.

## File map

| File | Role |
| --- | --- |
| `src/stub/__main__.py` | Allows `python -m stub` |
| `src/stub/cli.py` | Argument parsing and orchestration |
| `src/stub/config.py` | Read/write `config.toml` |
| `src/stub/templates.py` | Find, load, validate and scaffold templates |
| `src/stub/models.py` | Shared frozen pydantic models |
| `src/stub/render.py` | Placeholder substitution and message formatting |
| `src/stub/writer.py` | File creation and symlink management |
| `.templates/*.toml` | Output recipes |
| `config.toml` | Paths |
