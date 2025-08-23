from typing import List, Union
import argparse
from pydantic import BaseModel
from rich.console import Console
from rich.tree import Tree
from .models import Group, Command, Option


class Cli(BaseModel):
    """CLI model with methods."""

    name: str
    help: str = ""
    subgroups: List[Group] = []
    commands: List[Command] = []
    options: List[Option] = []
    max_width: int = 120

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
                    a_dest = arg.dest or arg.name
                    kwargs = {"help": arg.help, "type": arg.arg_type, "dest": a_dest}
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

    def run(self):
        """Run the CLI."""
        parser = self.build_parser()
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
            args.func(args)

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
        console.print(f"Description: {current.help}")
        console.print("Commands:")
        align_width = 40
        root_label = f"{self.name:<{align_width}} {self.help}"
        tree = Tree(root_label)
        self._add_children(tree, self, True, path, align_width)
        console.print(tree)

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
                flags = sorted(opt.flags, key=lambda f: (-len(f), f))
                opt_name = ", ".join(flags)
                opt_label = f"{opt_name:<{align_width}} {opt.help}"
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
                    child_label = self._get_label(child, align_width)
                    child_tree = current_tree.add(child_label)
                    self._add_children(
                        child_tree, child, True, remaining_path[1:], align_width
                    )
                    break
        else:
            for child in children:
                child_label = self._get_label(child, align_width)
                child_tree = current_tree.add(child_label)
                self._add_children(child_tree, child, False, [], align_width)

    def _get_label(self, node: Union[Group, Command], align_width: int) -> str:
        if isinstance(node, Group):
            return f"{node.name:<{align_width}} {node.help}"
        args_str = " ".join(
            f"[{arg.name.upper()}]"
            for arg in sorted(node.arguments, key=lambda x: (x.sort_key, x.name))
        )
        cmd_name = f"{node.name} {args_str}".rstrip()
        return f"{cmd_name:<{align_width}} {node.help}"
