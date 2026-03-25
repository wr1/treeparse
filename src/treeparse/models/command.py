"""command model."""

import inspect
from typing import Callable, List, Union, get_origin

from pydantic import BaseModel, computed_field

from .argument import argument
from .option import option


class command(BaseModel):
    """command model."""

    name: str
    help: str = ""
    callback: Callable[..., None]
    arguments: List[argument] = []
    options: List[option] = []
    sort_key: int = 0

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
        unwrapped = inspect.unwrap(self.callback)
        if inspect.iscoroutinefunction(unwrapped):
            raise ValueError(f"Callback for command '{self.name}' is async; treeparse does not support async callbacks")
        sig = inspect.signature(unwrapped)
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
            error_msg = f"Parameter name mismatch for command '{self.name}': "
            if missing:
                error_msg += f"Missing parameters in CLI definition: {missing}. "
            if extra:
                error_msg += f"Extra parameters in CLI definition: {extra}. "
            error_msg += f"Callback expects: {param_names}, CLI provides: {provided_names}"
            raise ValueError(error_msg)
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
                type_mismatches.append(f"{param}: callback {repr(p_type)} vs CLI {repr(cli_type)}")
        if type_mismatches:
            error_msg = f"Parameter type mismatch for command '{self.name}': " + "; ".join(type_mismatches)
            raise ValueError(error_msg)
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
