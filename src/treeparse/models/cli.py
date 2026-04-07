"""CLI model with methods."""

import argparse
import inspect
import json
import sys
import warnings
from enum import EnumMeta
from pathlib import Path
from typing import Callable, List, Optional, Union, get_origin

from pydantic import PrivateAttr, computed_field, model_validator
from rich.console import Console
from rich.syntax import Syntax

from ..utils.color_config import ColorTheme, color_config
from ..utils.help_renderer import help_renderer
from ..utils.helpers import load_yaml_config
from .argument import argument
from .chain import chain
from .command import command, _name_mismatch_error, _type_mismatch_error
from .group import group
from .option import option


def str2bool(v):
    """Convert string to boolean for argparse."""
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def chain_runner(chain_obj: chain, **kwargs):
    """Runner function for chain commands."""
    for sub_cmd in chain_obj.chained_commands:
        _, sig = sub_cmd._callback_sig
        sub_kwargs = {k: kwargs.get(k) for k in sig.parameters if k in kwargs}
        sub_cmd.callback(**sub_kwargs)


class RichArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser with rich-formatted errors."""

    def error(self, message):
        console = Console()
        if "invalid choice" in message:
            parts = message.split("invalid choice: ")
            if len(parts) > 1:
                invalid = parts[1].split(" (choose from")[0].strip("'")
                console.print(
                    f"[bold red]Error:[/bold red] {parts[0]}invalid choice: [yellow]'{invalid}'[/yellow] (choose from{parts[1].split('(choose from')[1]}"  # noqa: E501
                )
            else:
                console.print(f"[bold red]Error:[/bold red] {message}")
        else:
            console.print(f"[bold red]Error:[/bold red] {message}")
        self.exit(2)


class cli(group):
    """CLI model inheriting from group for sub-CLI composition."""

    max_width: int = 120
    theme: ColorTheme = ColorTheme.DEFAULT
    colors: color_config = color_config()
    show_types: bool = True
    show_defaults: bool = True
    line_connect: bool = False
    yml_config: Path = None
    callback: Optional[Callable[..., None]] = None
    version: Optional[str] = None

    _parser: Optional[argparse.ArgumentParser] = PrivateAttr(default=None)
    _max_depth: Optional[int] = PrivateAttr(default=None)

    @model_validator(mode="after")
    def set_colors_from_theme(self):
        self.colors = color_config.from_theme(self.theme)
        return self

    @property
    def is_flat(self) -> bool:
        """True when the CLI has no subcommands/groups (root acts as the command)."""
        return len(self.subgroups) == 0 and len(self.commands) == 0

    @computed_field
    @property
    def effective_arguments(self) -> List[argument]:
        return self.arguments

    @computed_field
    @property
    def effective_options(self) -> List[option]:
        return self.options

    def get_max_depth(self) -> int:
        """Compute max depth of CLI tree (cached after first call)."""
        if self._max_depth is not None:
            return self._max_depth

        def recurse(node: Union["cli", group, command, chain]) -> int:
            if isinstance(node, (command, chain)):
                return 0
            children = node.subgroups + node.commands if hasattr(node, "subgroups") else []
            if not children:
                return 0
            return 1 + max(recurse(c) for c in children)

        self._max_depth = recurse(self)
        return self._max_depth

    def _get_node_from_path(self, path: List[str]) -> Union[group, command, chain, "cli"]:
        """Get node from path."""
        current: Union["cli", group, command, chain] = self
        for p in path:
            if not hasattr(current, "subgroups"):
                raise ValueError(f"Path not found: {path}")
            children = current.subgroups + current.commands
            ch = next((c for c in children if c.display_name == p), None)
            if ch is None:
                raise ValueError(f"Path not found: {path}")
            current = ch
        return current

    def structure_dict(self):
        """Return a dictionary representation of the CLI structure."""

        def recurse(node: Union["cli", group, command, chain], is_root: bool = True):
            d = {"name": node.name, "help": node.help}
            if hasattr(node, "sort_key"):
                d["sort_key"] = node.sort_key
            node_opts = node.options if hasattr(node, "options") else []
            d["options"] = [
                {
                    **opt.model_dump(exclude={"arg_type"}),
                    "arg_type": opt.arg_type.__name__,
                    "choices": opt.choices,
                }
                for opt in sorted(node_opts, key=lambda x: x.sort_key)
            ]
            node_args = node.arguments if hasattr(node, "arguments") else []
            d["arguments"] = [
                {
                    **arg.model_dump(exclude={"arg_type"}),
                    "arg_type": arg.arg_type.__name__,
                    "choices": arg.choices,
                }
                for arg in sorted(node_args, key=lambda x: x.sort_key)
            ]
            if isinstance(node, command) or (isinstance(node, cli) and node.is_flat and node.callback is not None):
                d["type"] = "command"
                d["callback"] = node.callback.__name__
            elif isinstance(node, chain):
                d["type"] = "chain"
                d["chained"] = [recurse(c, False) for c in node.chained_commands]
            else:
                if is_root:
                    d["type"] = "cli"
                else:
                    d["type"] = "group"
            if hasattr(node, "subgroups"):
                d["subgroups"] = [recurse(g, is_root=False) for g in sorted(node.subgroups, key=lambda x: x.sort_key)]
            if hasattr(node, "commands"):
                d["commands"] = [recurse(c, is_root=False) for c in sorted(node.commands, key=lambda x: x.sort_key)]
            return d

        return recurse(self, is_root=True)

    def build_parser(self) -> argparse.ArgumentParser:
        """Build argparse parser from CLI structure (cached after first call).

        Do not mutate the cli after the first call to build_parser() or run().
        """
        if self._parser is not None:
            return self._parser
        self._validate()
        max_depth = self.get_max_depth()
        parser = RichArgumentParser(prog=self.display_name, description=self.help, add_help=False)
        self._add_args_and_opts_to_parser(parser, self.arguments, self.options)
        if self.is_flat:
            if self.callback is not None:
                parser.set_defaults(func=self.callback)
        else:
            self._build_subparser(parser, self, 1, max_depth, self.arguments, self.options)
        self._parser = parser
        return parser

    @staticmethod
    def _resolve_arg_type(arg_type):
        """Resolve arg_type to an argparse-compatible callable.

        Handles bool (str2bool), Enum subclasses (name lookup + auto-choices),
        and passes everything else through unchanged.
        Returns (type_callable, choices_or_None).
        """
        if arg_type is bool:
            return str2bool, None
        if isinstance(arg_type, EnumMeta):
            # argparse applies the type callable first, then checks choices.
            # choices must be enum members so that `member in choices` passes.
            # The converter raises ValueError (caught by argparse) on bad input.
            def _enum_conv(s, t=arg_type):
                try:
                    return t[s]
                except KeyError:
                    raise ValueError(s)

            return _enum_conv, list(arg_type)
        return arg_type, None

    def _add_args_and_opts_to_parser(self, parser: argparse.ArgumentParser, args: List[argument], opts: List[option]):
        for opt in opts:
            dest = opt.get_dest()
            if opt.flag:
                parser.add_argument(*opt.flags, action="store_true", dest=dest, help=opt.help)
                continue
            kwargs = {"dest": dest, "help": opt.help}
            if opt.default is not None:
                kwargs["default"] = opt.default
            type_callable, enum_choices = self._resolve_arg_type(opt.arg_type)
            kwargs["type"] = type_callable
            if opt.nargs is not None:
                kwargs["nargs"] = opt.nargs
            if opt.choices is not None:
                kwargs["choices"] = opt.choices
            elif enum_choices is not None:
                kwargs["choices"] = enum_choices
            if opt.required:
                kwargs["required"] = True
            parser.add_argument(*opt.flags, **kwargs)
        for arg in args:
            type_callable, enum_choices = self._resolve_arg_type(arg.arg_type)
            kwargs = {"help": arg.help, "type": type_callable}
            if arg.dest is not None:
                kwargs["dest"] = arg.dest
            if arg.nargs is not None:
                kwargs["nargs"] = arg.nargs
            if arg.default is not None:
                kwargs["default"] = arg.default
            elif arg.nargs == "?":
                kwargs["default"] = None
            if arg.choices is not None:
                kwargs["choices"] = arg.choices
            elif enum_choices is not None:
                kwargs["choices"] = enum_choices
            parser.add_argument(arg.name, **kwargs)

    def _build_subparser(
        self,
        parent_parser: argparse.ArgumentParser,
        node: Union["cli", group],
        depth: int,
        max_depth: int,
        inherited_args: List[argument],
        inherited_opts: List[option],
    ):
        if depth > max_depth:
            return
        # Filter inherited options to only those that should be inherited
        inheritable_inherited_opts = [opt for opt in inherited_opts if opt.inherit]
        children = sorted(
            (node.subgroups + node.commands) if hasattr(node, "subgroups") else [],
            key=lambda x: x.sort_key,
        )
        if children:
            subparsers = parent_parser.add_subparsers(dest=f"command_{depth}")
            for child in children:
                child_parser = subparsers.add_parser(child.display_name, help=child.help, add_help=False)
                if isinstance(child, group):
                    self._add_args_and_opts_to_parser(
                        child_parser,
                        inherited_args + child.arguments,
                        inheritable_inherited_opts + child.options,
                    )
                    self._build_subparser(
                        child_parser,
                        child,
                        depth + 1,
                        max_depth,
                        inherited_args + child.arguments,
                        inheritable_inherited_opts + child.options,
                    )
                else:  # command or chain
                    self._add_args_and_opts_to_parser(
                        child_parser,
                        child.effective_arguments,
                        child.effective_options,  # Removed inheritable_inherited_opts to prevent default override
                    )
                    if isinstance(child, command):
                        child_parser.set_defaults(func=child.callback)
                    else:
                        child_parser.set_defaults(func=chain_runner, chain_obj=child)

    def _validate(self):
        """Validate all commands in the CLI structure, considering inherited options and arguments."""
        if self.is_flat and self.callback is not None:
            # Reuse the exact validation logic from command (no duplication)
            temp = command(
                name=self.name,
                help=self.help,
                callback=self.callback,
                arguments=self.arguments,
                options=self.options,
            )
            temp.validate()
            return

        def recurse(
            node: Union["cli", group, command, chain],
            inherited_args: List[argument] = [],
            inherited_opts: List[option] = [],
        ):
            if isinstance(node, command):
                # Filter inherited options to only those that should be inherited
                inheritable_opts = [opt for opt in inherited_opts if opt.inherit]
                effective_args = inherited_args + node.arguments
                effective_opts = inheritable_opts + node.options
                provided = {}
                for arg in effective_args:
                    dest = arg.dest or arg.name
                    arg_type = arg.arg_type
                    if arg.nargs in ["*", "+"]:
                        arg_type = List[arg_type]
                    provided[dest] = arg_type
                for opt in effective_opts:
                    dest = opt.get_dest()
                    opt_type = opt.arg_type
                    if opt.nargs in ["*", "+"]:
                        opt_type = List[opt_type]
                    provided[dest] = opt_type
                unwrapped_cb, sig = node._callback_sig
                if inspect.iscoroutinefunction(unwrapped_cb):
                    raise ValueError(
                        f"Callback for command '{node.name}' is async; treeparse does not support async callbacks"
                    )
                param_names = set(sig.parameters.keys())
                param_types = {
                    k: v.annotation for k, v in sig.parameters.items() if v.annotation != inspect.Parameter.empty
                }
                provided_names = set(provided.keys())
                if param_names != provided_names:
                    missing = param_names - provided_names
                    extra = provided_names - param_names
                    raise ValueError(
                        _name_mismatch_error(node.name, unwrapped_cb.__name__, sig, provided, missing, extra)
                    )
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
                    elif cli_type != p_type:
                        type_mismatches.append((param, p_type, cli_type))
                if type_mismatches:
                    raise ValueError(_type_mismatch_error(node.name, unwrapped_cb.__name__, sig, type_mismatches))
                # Check defaults against choices (only local)
                for arg in node.arguments:
                    if arg.choices is not None and arg.default is not None:
                        if arg.nargs in ["*", "+"] and isinstance(arg.default, list):
                            for d in arg.default:
                                if d not in arg.choices:
                                    raise ValueError(
                                        f"Default value {d} not in choices {arg.choices} for argument '{arg.name}' in command '{node.name}'"  # noqa: E501
                                    )
                        else:
                            if arg.default not in arg.choices:
                                raise ValueError(
                                    f"Default value {arg.default} not in choices {arg.choices} for argument '{arg.name}' in command '{node.name}'"  # noqa: E501
                                )
                for opt in effective_opts:
                    if opt.choices is not None and opt.default is not None:
                        if opt.nargs in ["*", "+"] and isinstance(opt.default, list):
                            for d in opt.default:
                                if d not in opt.choices:
                                    raise ValueError(
                                        f"Default value {d} not in choices {opt.choices} for option '{opt.flags[0]}' in command '{node.name}'"  # noqa: E501
                                    )
                        else:
                            if opt.default not in opt.choices:
                                raise ValueError(
                                    f"Default value {opt.default} not in choices {opt.choices} for option '{opt.flags[0]}' in command '{node.name}'"  # noqa: E501
                                )
            elif isinstance(node, chain):
                node.validate()
            else:
                for cmd in node.commands:
                    recurse(
                        cmd,
                        inherited_args + node.arguments,
                        inherited_opts + node.options,
                    )
                for grp in node.subgroups:
                    recurse(
                        grp,
                        inherited_args + node.arguments,
                        inherited_opts + node.options,
                    )

        recurse(self, [], [])

    def _apply_yaml_config(self, config: dict):
        """Walk the full CLI tree and apply config overrides to all options by dest.

        Emits warnings for unrecognized config keys.
        """

        seen_keys = set()

        def walk(node):
            if hasattr(node, "options"):
                for opt in node.options:
                    dest = opt.get_dest()
                    if dest in config:
                        opt.default = config[dest]
                        seen_keys.add(dest)
            if hasattr(node, "subgroups"):
                for g in node.subgroups:
                    walk(g)
            if hasattr(node, "commands"):
                for c in node.commands:
                    walk(c)

        walk(self)
        for key in config:
            if key not in seen_keys:
                warnings.warn(
                    f"treeparse YAML config: unrecognized key '{key}'",
                    UserWarning,
                    stacklevel=4,
                )

    def run(self):
        """Run the CLI."""
        console = Console()
        # Load YAML config before building parser so defaults take effect
        if self.yml_config:
            config = load_yaml_config(str(self.yml_config))
            self._apply_yaml_config(config)
            # Invalidate parser cache so new defaults are picked up
            self._parser = None
            self._max_depth = None
        try:
            parser = self.build_parser()
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] {e}", highlight=False)
            sys.exit(1)
        # Handle special flags
        argv = sys.argv[1:]
        version_flags = ["--version", "-V"]
        has_version = any(a in version_flags for a in argv)
        if has_version:
            v = self._resolve_version()
            if v:
                console.print(v)
            sys.exit(0)
        help_flags = ["--help", "-h"]
        json_flags = ["--json", "-j"]
        has_help = any(a in help_flags for a in argv)
        has_json = any(a in json_flags for a in argv)
        if has_help or has_json:
            if has_json:
                structure = self.structure_dict()
                json_str = json.dumps(structure, indent=2)
                syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
                console.print(syntax)
            else:
                path = []
                for a in argv:
                    if a in help_flags:
                        break
                    if not a.startswith("-"):
                        path.append(a)
                self.print_help(path)
            sys.exit(0)
        # Normal parsing
        try:
            args = parser.parse_args()
        except SystemExit:
            sys.exit(1)
        path = []
        for i in range(1, self.get_max_depth() + 2):
            cmd = getattr(args, f"command_{i}", None)
            if cmd is None:
                break
            path.append(cmd)
        if not hasattr(args, "func"):
            self.print_help(path)
            sys.exit(0)
        current = self._get_node_from_path(path)
        missing = []
        for arg in current.effective_arguments:
            dest = arg.dest or arg.name
            if arg.nargs is None and arg.default is None and getattr(args, dest, None) is None:
                missing.append(arg.name)
        if missing:
            parser.error("the following arguments are required: " + ", ".join(missing))
        # Collect effective args and opts from the path
        effective_args = []
        effective_opts = []
        path_nodes = [self]
        current_node = self
        for p in path:
            children = current_node.subgroups + current_node.commands
            child = next((c for c in children if c.display_name == p), None)
            if child:
                path_nodes.append(child)
                current_node = child
        for node in path_nodes:
            if hasattr(node, "arguments"):
                effective_args.extend(node.arguments)
            else:
                effective_args.extend(node.effective_arguments)
            if hasattr(node, "options"):
                effective_opts.extend(node.options)
            else:
                effective_opts.extend(node.effective_options)
        # For the current node, add inherited options from ancestors
        if isinstance(current, (command, chain)):
            for node in path_nodes[:-1]:
                effective_opts.extend([opt for opt in node.options if opt.inherit])
        # Collect all options from the CLI
        all_options = []

        def collect_opts(node):
            if hasattr(node, "options"):
                all_options.extend(node.options)
            if hasattr(node, "subgroups"):
                for g in node.subgroups:
                    collect_opts(g)
            if hasattr(node, "commands"):
                for c in node.commands:
                    collect_opts(c)

        collect_opts(self)
        provided_names = set()
        for opt in all_options:
            provided_names.add(opt.get_dest())
        for arg in effective_args:
            provided_names.add(arg.dest or arg.name)
        arg_dict = {
            k: v
            for k, v in vars(args).items()
            if not k.startswith("command_") and k not in ("func", "chain_obj") and k in provided_names
        }
        if hasattr(args, "chain_obj"):
            args.func(args.chain_obj, **arg_dict)
        else:
            args.func(**arg_dict)

    def _resolve_version(self) -> Optional[str]:
        if self.version is not None:
            return self.version
        try:
            from importlib.metadata import version as _pkg_version
            return _pkg_version(self.name)
        except Exception:
            return None

    def print_help(self, path: List[str]):
        """Print custom tree help."""
        help_renderer(self).render(path)
