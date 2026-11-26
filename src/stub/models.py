"""Pydantic models shared by stub's modules."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StubError(Exception):
    """An error meant for the user, without a traceback."""


class FrozenModel(BaseModel):
    """Base for models that should never change after creation."""

    model_config = ConfigDict(frozen=True)


class Paths(FrozenModel):
    """The two directories stub cares about."""

    learnings: Path
    vault: Path | None = None


class TemplateSpec(FrozenModel):
    """One parsed .toml recipe from .templates/."""

    name: str
    extension: str
    body: str
    filename: str = "{date}_{language}"

    @field_validator("extension", mode="before")
    @classmethod
    def strip_leading_dot(cls, value: str) -> str:
        return value.lstrip(".") if isinstance(value, str) else value

    @classmethod
    def from_mapping(cls, data: dict, source: Path | None = None) -> TemplateSpec:
        origin = f" in {source}" if source else ""
        for key in ("name", "extension", "body"):
            if key not in data:
                raise StubError(f"template{origin} is missing required key '{key}'")
        if not all(isinstance(data[key], str) for key in ("name", "extension", "body")):
            raise StubError(f"template{origin} has a non-string name, extension or body")
        filename = data.get("filename", "{date}_{language}")
        if not isinstance(filename, str):
            raise StubError(f"template{origin} has a non-string filename pattern")
        return cls(
            name=data["name"],
            extension=data["extension"],
            body=data["body"],
            filename=filename,
        )


class RenderContext(FrozenModel):
    """Everything render.py needs to fill in a template."""

    date: str
    time: str
    timestamp: str
    language: str
    name: str
    filename: str
    message: str | None = None

    @classmethod
    def create(
        cls,
        *,
        language: str,
        name: str,
        filename: str,
        message: str | None = None,
        now: datetime | None = None,
    ) -> RenderContext:
        now = now or datetime.now()
        return cls(
            date=now.strftime("%Y-%m-%d"),
            time=now.strftime("%H:%M:%S"),
            timestamp=now.isoformat(timespec="seconds"),
            language=language,
            name=name,
            filename=filename,
            message=message,
        )

    def mapping(self) -> dict[str, str]:
        """Values for string.Template, with the message shaped per output type."""
        message = self.message or ""
        return {
            "DATE": self.date,
            "TIME": self.time,
            "TIMESTAMP": self.timestamp,
            "LANGUAGE": self.language,
            "NAME": self.name,
            "FILENAME": self.filename,
            "TITLE": f"{self.date} {self.language}",
            "MESSAGE_MD": f"_{message}_" if message else "",
            "MESSAGE_COMMENT": f"// {message}" if message else "",
        }


class GenerationResult(FrozenModel):
    """What a generate run produced, for printing and for tests."""

    files: tuple[Path, ...] = Field(default_factory=tuple)
    symlinks: tuple[Path, ...] = Field(default_factory=tuple)


def safe_stem(name: str) -> str:
    """Turn a user-supplied name into a single safe filename stem."""
    stem = re.sub(r"[\s/\\]+", "_", name.strip()).strip("._")
    if not stem:
        raise StubError("name must contain at least one character")
    return stem


def format_stem(pattern: str, *, date: str, language: str, name: str) -> str:
    """Expand a template's filename pattern into a safe stem."""
    try:
        stem = pattern.format(date=date, language=language, name=name)
    except (KeyError, IndexError, ValueError) as exc:
        raise StubError(f"bad filename pattern {pattern!r}: {exc}") from exc
    return safe_stem(stem)
