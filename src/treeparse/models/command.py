"""command model."""

import inspect
from typing import Any, Callable, List, Union, get_origin

from pydantic import BaseModel, PrivateAttr, computed_field

from .argument import argument
from .option import option


def _fmt_type(t) -> str:
    return getattr(t, "__name__", str(t))


def _name_mismatch_error(
    cmd_name: str,
    cb_name: str,
    sig: inspect.Signature,
    provided: dict,
    missing: set,
    extra: set,
) -> str:
    cb_params = ", ".join(
        (f"{p}: {_fmt_type(v.annotation)}" if v.annotation != inspect.Parameter.empty else p)
        for p, v in sig.parameters.items()
    )
    cli_parts = [f"{dest} ({_fmt_type(t)})" for dest, t in sorted(provided.items())]
    lines = [
        f"[CLI DEFINITION ERROR] command '{cmd_name}': parameter name mismatch",
        "",
        f"  callback : def {cb_name}({cb_params})",
        f"  CLI      : {', '.join(cli_parts) if cli_parts else '(none)'}",
        "",
    ]
    if missing:
        lines.append("  In callback but missing from CLI definition:")
        for p in sorted(missing):
            ann = sig.parameters[p].annotation
            t_hint = _fmt_type(ann) if ann != inspect.Parameter.empty else "?"
            lines.append(
                f"    - '{p}' ({t_hint})  →  add argument(name='{p}', arg_type={t_hint})"
                f" or option(flags=['--{p}'], arg_type={t_hint})"
            )
    if extra:
        lines.append("  In CLI but not in callback:")
        for p in sorted(extra):
            lines.append(f"    - '{p}'  →  remove or rename to match a callback parameter")
    lines += ["", "  Every callback parameter name must match exactly one argument/option dest."]
    return "\n".join(lines)


def _type_mismatch_error(
    cmd_name: str,
    cb_name: str,
    sig: inspect.Signature,
    mismatches: list,
) -> str:
    cb_params = ", ".join(
        (f"{p}: {_fmt_type(v.annotation)}" if v.annotation != inspect.Parameter.empty else p)
        for p, v in sig.parameters.items()
    )
    lines = [
        f"[CLI DEFINITION ERROR] command '{cmd_name}': parameter type mismatch",
        "",
        f"  callback: def {cb_name}({cb_params})",
        "",
        "  Type mismatches:",
    ]
    for param, cb_type, cli_type in mismatches:
        lines.append(f"    - '{param}': callback expects {_fmt_type(cb_type)}, CLI defines {_fmt_type(cli_type)}")
        lines.append(f"      Fix: change arg_type={_fmt_type(cli_type)} → arg_type={_fmt_type(cb_type)}")
    lines += ["", "  Set arg_type= in the argument/option definition to match the callback annotation."]
    return "\n".join(lines)


class command(BaseModel):
    """command model."""

    name: str
    help: str = ""
    callback: Callable[..., None]
    arguments: List[argument] = []
    options: List[option] = []
    sort_key: int = 0

    _unwrapped_cb: Any = PrivateAttr(default=None)
    _sig: Any = PrivateAttr(default=None)

    @property
    def _callback_sig(self):
        if self._unwrapped_cb is None:
            self._unwrapped_cb = inspect.unwrap(self.callback)
            self._sig = inspect.signature(self._unwrapped_cb)
        return self._unwrapped_cb, self._sig

    @computed_field
    @property
    def display_name(self) -> str:
        """Get display name."""
        return self.name

    @computed_field
    @property
    def effective_arguments(self) -> List[argument]:
        return self.arguments

    @computed_field
    @property
    def effective_options(self) -> List[option]:
        return self.options

    def validate(self):
        """Validate that callback parameters match defined arguments and options in name and type."""
        unwrapped, sig = self._callback_sig
        if inspect.iscoroutinefunction(unwrapped):
            raise ValueError(f"Callback for command '{self.name}' is async; treeparse does not support async callbacks")
        param_names = set(sig.parameters.keys())
        param_types = {k: v.annotation for k, v in sig.parameters.items() if v.annotation != inspect.Parameter.empty}
        provided = {}
        for arg in self.arguments:
            dest = arg.dest or arg.name
            arg_type = arg.arg_type
            if arg.nargs in ["*", "+"]:
                arg_type = List[arg_type]
            provided[dest] = arg_type
        for opt in self.options:
            dest = opt.get_dest()
            opt_type = opt.arg_type
            if opt.nargs in ["*", "+"]:
                opt_type = List[opt_type]
            provided[dest] = opt_type
        provided_names = set(provided.keys())
        if param_names != provided_names:
            missing = param_names - provided_names
            extra = provided_names - param_names
            raise ValueError(
                _name_mismatch_error(self.name, unwrapped.__name__, sig, provided, missing, extra)
            )
        # Check types
        type_mismatches = []
        for param, p_type in param_types.items():
            cli_type = provided.get(param)
            # Handle list vs List equivalence
            if p_type is list and str(cli_type).startswith("typing.List"):
                continue  # Consider them equivalent
            if str(p_type).startswith("typing.List") and cli_type is list:
                continue
            # Skip type check for Union types to allow flexibility
            if get_origin(p_type) is Union:
                continue
            if cli_type != p_type:
                type_mismatches.append((param, p_type, cli_type))
        if type_mismatches:
            raise ValueError(_type_mismatch_error(self.name, unwrapped.__name__, sig, type_mismatches))
        # Check defaults against choices
        for arg in self.arguments:
            if arg.choices is not None and arg.default is not None:
                if arg.nargs in ["*", "+"] and isinstance(arg.default, list):
                    for d in arg.default:
                        if d not in arg.choices:
                            raise ValueError(
                                f"Default value {d} not in choices {arg.choices} for argument '{arg.name}' in command '{self.name}'"  # noqa: E501
                            )
                else:
                    if arg.default not in arg.choices:
                        raise ValueError(
                            f"Default value {arg.default} not in choices {arg.choices} for argument '{arg.name}' in command '{self.name}'"  # noqa: E501
                        )
        for opt in self.options:
            if opt.choices is not None and opt.default is not None:
                if opt.nargs in ["*", "+"] and isinstance(opt.default, list):
                    for d in opt.default:
                        if d not in opt.choices:
                            raise ValueError(
                                f"Default value {d} not in choices {opt.choices} for option '{opt.flags[0]}' in command '{self.name}'"  # noqa: E501
                            )
                else:
                    if opt.default not in opt.choices:
                        raise ValueError(
                            f"Default value {opt.default} not in choices {opt.choices} for option '{opt.flags[0]}' in command '{self.name}'"  # noqa: E501
                        )
