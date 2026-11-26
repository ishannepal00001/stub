"""Fill a template's ${...} blanks with a RenderContext."""

from __future__ import annotations

from string import Template

from .models import RenderContext, TemplateSpec

_MESSAGE_LINES = {"${MESSAGE_MD}", "${MESSAGE_COMMENT}"}


def render(spec: TemplateSpec, context: RenderContext) -> str:
    """Substitute placeholders; drop message lines when there is no message."""
    values = context.mapping()
    lines: list[str] = []
    for line in spec.body.splitlines():
        stripped = line.strip()
        if stripped in _MESSAGE_LINES and not values[stripped[2:-1]]:
            continue
        lines.append(Template(line).safe_substitute(values))
    return "\n".join(lines).rstrip() + "\n"
