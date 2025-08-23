from typing import List, Union
import argparse
import sys
from pydantic import BaseModel
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from .models import Group, Command, Option, ColorConfig


class Cli(BaseModel):
    """CLI model with methods."""

    name: str
    help: str = ""
    subgroups: List[Group] = []
    commands: List[Command] = []
    options: List[Option] = []
    max_width: int = 120
    color_config: ColorConfig = ColorConfig()

    def get_max_depth(self) -> int:
        """Compute max depth of CLI tree."""

        def recurse(node: Union["Cli", Group, Command]) -> int:
            if isinstance(node, Command):
                return 0
            children = (
                node.subgroups + node.commands if hasattr(node, "subgroups") else []
            )
            if not children:
                return 0
            return 1 + max(recurse(c) for c in children)

        return recurse(self)

    def build_parser(self) -> argparse.ArgumentParser:
        """Build argparse parser from CLI structure."""
        self._validate()
        max_depth = self.get_max_depth()
        parser = argparse.ArgumentParser(
            prog=self.name, description=self.help, add_help=False
        )
        for opt in self.options:
            dest = opt.dest or opt.flags[0].lstrip("-").replace("-", "_")
            kwargs = {"dest": dest, "help": opt.help, "default": opt.default}
            if opt.is_flag:
                kwargs["action"] = "store_true"
            else:
                kwargs["type"] = opt.arg_type
            parser.add_argument(*opt.flags, **kwargs)
        parser.add_argument("--help", "-h", action="store_true")
        self._build_subparser(parser, self, 1, max_depth)
        return parser

    def _build_subparser(
        self,
        parent_parser: argparse.ArgumentParser,
        node: Union["Cli", Group],
        depth: int,
        max_depth: int,
    ):
        if depth > max_depth:
            return
        subparsers = parent_parser.add_subparsers(dest=f"command_{depth}")
        children = sorted(
            node.subgroups + node.commands, key=lambda x: (x.sort_key, x.name)
        )
        for child in children:
            child_parser = subparsers.add_parser(
                child.name, help=child.help, add_help=False
            )
            for opt in child.options:
                dest = opt.dest or opt.flags[0].lstrip("-").replace("-", "_")
                kwargs = {"dest": dest, "help": opt.help, "default": opt.default}
                if opt.is_flag:
                    kwargs["action"] = "store_true"
                else:
                    kwargs["type"] = opt.arg_type
                child_parser.add_argument(*opt.flags, **kwargs)
            child_parser.add_argument("--help", "-h", action="store_true")
            if isinstance(child, Command):
                for arg in child.arguments:
                    kwargs = {"help": arg.help, "type": arg.arg_type}
                    if arg.dest is not None:
                        kwargs["dest"] = arg.dest
                    if arg.nargs is not None:
                        kwargs["nargs"] = arg.nargs
                    if arg.default is not None:
                        kwargs["default"] = arg.default
                    elif arg.nargs == "?":
                        kwargs["default"] = None
                    child_parser.add_argument(arg.name, **kwargs)
                child_parser.set_defaults(func=child.callback)
            else:
                self._build_subparser(child_parser, child, depth + 1, max_depth)

    def _validate(self):
        """Validate all commands in the CLI structure."""

        def recurse(node: Union["Cli", Group, Command]):
            if isinstance(node, Command):
                node.validate()
            else:
                for cmd in node.commands:
                    recurse(cmd)
                for grp in node.subgroups:
                    recurse(grp)

        recurse(self)

    def run(self):
        """Run the CLI."""
        try:
            parser = self.build_parser()
        except ValueError as e:
            print(str(e))
            sys.exit(1)
        args = parser.parse_args()
        path = []
        for i in range(1, self.get_max_depth() + 2):
            cmd = getattr(args, f"command_{i}", None)
            if cmd is None:
                break
            path.append(cmd)
        if getattr(args, "help", False) or not hasattr(args, "func"):
            self.print_help(path)
        else:
            # Extract relevant args, excluding internal ones
            arg_dict = {
                k: v
                for k, v in vars(args).items()
                if not k.startswith("command_") and k not in ("func", "help")
            }
            args.func(**arg_dict)

    def print_help(self, path: List[str]):
        """Print custom tree help."""
        console = Console(width=self.max_width)
        path_str = " ".join(path)
        if path_str:
            path_str += " "
        usage = f"Usage: {self.name} {path_str}[OPTIONS] COMMAND [ARGS]..."
        console.print(usage)
        current = self
        for p in path:
            ch = next(
                c
                for c in (
                    current.subgroups + current.commands
                    if hasattr(current, "subgroups")
                    else []
                )
                if c.name == p
            )
            current = ch
        console.print(
            f"[{self.color_config.requested_help}]Description: {current.help}[/{self.color_config.requested_help}]"
        )
        console.print("Commands:")
        align_width = self._compute_max_name_length(path)
        root_label = self._get_root_label(align_width)
        tree = Tree(root_label)
        self._add_children(tree, self, True, path, align_width)
        console.print(tree)

    def _compute_max_name_length(self, path: List[str]) -> int:
        """Compute maximum name length for alignment in the visible tree."""
        max_len = 0
        current = self
        for p in path:
            current = next(
                c
                for c in (
                    current.subgroups + current.commands
                    if hasattr(current, "subgroups")
                    else []
                )
                if c.name == p
            )

        def recurse(
            node: Union["Cli", Group, Command], on_path: bool, remaining_path: List[str]
        ):
            nonlocal max_len
            if not isinstance(node, Cli):
                opts = sorted(node.options, key=lambda x: (x.sort_key, x.flags[0]))
                for opt in opts:
                    flags = sorted(opt.flags, key=lambda f: (-len(f), f))
                    opt_name = ", ".join(flags)
                    max_len = max(max_len, len(opt_name))
            if isinstance(node, Command):
                return
            children = sorted(
                (node.subgroups + node.commands) if hasattr(node, "subgroups") else [],
                key=lambda x: (x.sort_key, x.name),
            )
            if on_path and remaining_path:
                next_name = remaining_path[0]
                for child in children:
                    if child.name == next_name:
                        name_part = self._get_name_part(child)
                        max_len = max(max_len, len(name_part))
                        recurse(child, True, remaining_path[1:])
                        break
            else:
                for child in children:
                    name_part = self._get_name_part(child)
                    max_len = max(max_len, len(name_part))
                    recurse(child, False, [])

        recurse(self, True, path)  # Start from root
        max_len = max(max_len, len(self.name))
        return max_len

    def _get_name_part(self, node: Union[Group, Command]) -> str:
        if isinstance(node, Group):
            return node.name
        args_str = " ".join(
            f"[{arg.name.upper()}]"
            for arg in sorted(node.arguments, key=lambda x: (x.sort_key, x.name))
        )
        return f"{node.name} {args_str}".rstrip()

    def _get_root_label(self, align_width: int) -> Text:
        label = Text()
        label.append(self.name, style=self.color_config.app)
        name_len = label.cell_len
        padding = align_width - name_len
        if padding > 0:
            label.append(" " * padding)
        if self.help:
            label.append(" ")
            label.append(self.help, style=self.color_config.normal_help)
        return label

    def _get_label(
        self, node: Union[Group, Command], align_width: int, on_path: bool
    ) -> Text:
        help_style = (
            self.color_config.requested_help
            if on_path
            else self.color_config.normal_help
        )
        label = Text()
        if isinstance(node, Group):
            label.append(node.name, style=self.color_config.group)
        else:
            label.append(node.name, style=self.color_config.command)
            for arg in sorted(node.arguments, key=lambda x: (x.sort_key, x.name)):
                label.append(" ")
                label.append(f"[{arg.name.upper()}]", style=self.color_config.argument)
        name_len = label.cell_len
        padding = align_width - name_len
        if padding > 0:
            label.append(" " * padding)
        if node.help:
            label.append(" ")
            label.append(node.help, style=help_style)
        return label

    def _get_option_label(self, opt: Option, align_width: int) -> Text:
        label = Text()
        flags = sorted(opt.flags, key=lambda f: (-len(f), f))
        flags_str = ", ".join(flags)
        label.append(flags_str, style=self.color_config.option)
        name_len = label.cell_len
        padding = align_width - name_len
        if padding > 0:
            label.append(" " * padding)
        if opt.help:
            label.append("    ")
            label.append(opt.help, style=self.color_config.option_help)
        return label

    def _add_children(
        self,
        current_tree: Tree,
        node: Union["Cli", Group, Command],
        on_path: bool,
        remaining_path: List[str],
        align_width: int,
    ):
        if not isinstance(node, Cli):
            opts = sorted(node.options, key=lambda x: (x.sort_key, x.flags[0]))
            for opt in opts:
                opt_label = self._get_option_label(opt, align_width)
                current_tree.add(opt_label)
        if isinstance(node, Command):
            return
        children = sorted(
            (node.subgroups + node.commands) if hasattr(node, "subgroups") else [],
            key=lambda x: (x.sort_key, x.name),
        )
        if on_path and remaining_path:
            next_name = remaining_path[0]
            for child in children:
                if child.name == next_name:
                    child_label = self._get_label(child, align_width, True)
                    child_tree = current_tree.add(child_label)
                    self._add_children(
                        child_tree, child, True, remaining_path[1:], align_width
                    )
                    break
        else:
            for child in children:
                child_label = self._get_label(child, align_width, False)
                child_tree = current_tree.add(child_label)
                self._add_children(child_tree, child, False, [], align_width)
