"""option model."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, model_validator


class option(BaseModel):
    """option model."""

    flags: list[str]
    dest: str | None = None
    arg_type: Any = str
    help: str = ""
    default: Any = None
    nargs: int | str | None = None
    choices: list[Any] | None = None
    sort_key: int = 0
    required: bool = False
    inherit: bool = True
    flag: bool = False

    @model_validator(mode="after")
    def check_required_default_contradiction(self):
        if self.required and self.default is not None:
            raise ValueError(
                f"option {self.flags!r}: required=True is contradicted by default={self.default!r}; "
                "argparse ignores required when a default exists"
            )
        if self.flag and self.required:
            raise ValueError(
                f"option {self.flags!r}: flag=True is incompatible with required=True; flags are always optional"
            )
        if self.flag and self.nargs is not None:
            raise ValueError(
                f"option {self.flags!r}: flag=True is incompatible with nargs={self.nargs!r}; flags take no value"
            )
        if self.flag:
            self.arg_type = bool
        return self

    @property
    def sorted_flags(self) -> list[str]:
        return sorted(self.flags, key=lambda f: (-len(f), f))

    def get_dest(self) -> str:
        """Compute the destination name for this option."""
        if self.dest:
            return self.dest
        long_flags = [f for f in self.flags if f.startswith("--")]
        if long_flags:
            return long_flags[0].lstrip("--").replace("-", "_")
        if self.flags:
            return self.flags[0].lstrip("-").replace("-", "_")
        raise ValueError("No flags defined for option")
