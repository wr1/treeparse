"""Positional argument model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class argument(BaseModel):
    """Positional argument model."""

    name: str
    dest: str | None = None
    arg_type: Any = str
    help: str = ""
    nargs: int | str | None = None
    default: Any = None
    choices: list[Any] | None = None
    sort_key: int = 0
    show_type: bool = True
