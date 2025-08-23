from typing import List, Union
import argparse
import sys
from pydantic import BaseModel
from rich.console import Console
from rich.tree import Tree
from rich.text import Text
from .models import Group, Command, Option, Argument, ColorConfig

class Cli(BaseModel):
    """CLI model with methods."""
    name: str
    help: str = ""
    subgroups: List[Group] = []
    commands: List[Command] = []
    options: List[Option] = []
    max_width: int = 120
    color_config: ColorConfig = ColorConfig()
    show_types: bool = False

    def get_max_depth(self) -> int:
        """Compute max depth of CLI tree."""
        def recurse(node: Union["Cli", Group, Command]) -> int:
            if isinstance(node, Command):
                return 0
            children = node.subgroups + node.commands if hasattr(node, "subgroups") else []
            if not children:
                return 0
            return 1 + max(recurse(c) for c in children)
        return recurse(self)

    def build_parser(self) -> argparse.ArgumentParser:
        """Build argparse parser from CLI structure."""
        self._validate()
        max_depth = self.get_max_depth()
        parser = argparse.ArgumentParser(prog=self.name, description=self.help, add_help=False)
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

    def _build_subparser(self, parent_parser: argparse.ArgumentParser, node: Union["Cli", Group], depth: int, max_depth: int):
        if depth > max_depth:
            return
        subparsers = parent_parser.add_subparsers(dest=f"command_{depth}")
        children = sorted(node.subgroups + node.commands, key=lambda x: (x.sort_key, x.name))
        for child in children:
            child_parser = subparsers.add_parser(child.name, help=child.help, add_help=False)
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
            console = Console()
            console.print(str(e), markup=True)
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
            arg_dict = {k: v for k, v in vars(args).items() if not k.startswith('command_') and k not in ('func', 'help')}
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
            ch = next(c for c in (current.subgroups + current.commands if hasattr(current, 'subgroups') else []) if c.name == p)
            current = ch
        console.print(f"[{self.color_config.requested_help}]Description: {current.help}[/{self.color_config.requested_help}]")
        console.print("Commands:")
        max_start = 0
        def collect_recurse(node: Union["Cli", Group, Command], on_path: bool, remaining_path: List[str], depth: int):
            nonlocal max_start
            if isinstance(node, Cli):
                name_len = len(node.name)
            else:
                name_len = len(self._get_name_part(node))
            prefix_len = depth * 4
            max_start = max(max_start, prefix_len + name_len)
            if not isinstance(node, Cli):
                opts = sorted(node.options, key=lambda x: (x.sort_key, x.flags[0]))
                for opt in opts:
                    flags = sorted(opt.flags, key=lambda f: (-len(f), f))
                    opt_name = ", ".join(flags)
                    opt_len = len(opt_name)
                    if self.show_types:
                        type_name = 'bool' if opt.is_flag else opt.arg_type.__name__
                        opt_len += len(f":{type_name}")
                    opt_prefix = (depth + 1) * 4
                    max_start = max(max_start, opt_prefix + opt_len)
            if isinstance(node, Command):
                return
            children = sorted((node.subgroups + node.commands) if hasattr(node, 'subgroups') else [], key=lambda x: (x.sort_key, x.name))
            if on_path and remaining_path:
                next_name = remaining_path[0]
                for child in children:
                    if child.name == next_name:
                        collect_recurse(child, True, remaining_path[1:], depth + 1)
                        break
            else:
                for child in children:
                    collect_recurse(child, False, [], depth + 1)
        collect_recurse(self, True, path, 0)
        selected_depth = len(path)
        root_label = self._get_root_label(max_start, 0, True)
        tree = Tree(root_label)
        self._add_children(tree, self, True, path, max_start, 0, selected_depth)
        console.print(tree)

    def _get_name_part(self, node: Union[Group, Command]) -> str:
        if isinstance(node, Group):
            return node.name
        args_str = " ".join(f"[{arg.name.upper()},{arg.arg_type.__name__}]" if self.show_types else f"[{arg.name.upper()}]" for arg in sorted(node.arguments, key=lambda x: (x.sort_key, x.name)))
        return f"{node.name} {args_str}".rstrip()

    def _wrap_help(self, help: str, width: int) -> List[str]:
        if width <= 0:
            width = 20
        lines = []
        current = []
        current_len = 0
        words = help.split()
        for word in words:
            word_len = len(word)
            if current and current_len + 1 + word_len > width:
                lines.append(' '.join(current))
                current = [word]
                current_len = word_len
            else:
                if current:
                    current_len += 1
                current.append(word)
                current_len += word_len
        if current:
            lines.append(' '.join(current))
        return lines

    def _get_root_label(self, max_start: int, depth: int, is_ancestor: bool) -> Text:
        style = "dim " + self.color_config.app if is_ancestor else self.color_config.app
        label = Text()
        label.append(self.name, style=style)
        name_len = len(self.name)
        prefix_len = depth * 4
        padding = max_start - prefix_len - name_len
        label.append(" " * padding)
        if self.help:
            label.append(" ")
            help_lines = self._wrap_help(self.help, self.max_width - (max_start + 1))
            label.append(help_lines[0], style=self.color_config.normal_help)
            for hl in help_lines[1:]:
                label.append("\n")
                label.append(" " * (name_len + padding + 1))
                label.append(hl, style=self.color_config.normal_help)
        return label

    def _get_label(self, node: Union[Group, Command], max_start: int, on_path: bool, depth: int, is_ancestor: bool) -> Text:
        help_style = self.color_config.requested_help if on_path else self.color_config.normal_help
        name_style = "dim " + self.color_config.group if is_ancestor and isinstance(node, Group) else self.color_config.group if isinstance(node, Group) else "dim " + self.color_config.command if is_ancestor else self.color_config.command
        arg_style = "dim " + self.color_config.argument if is_ancestor else self.color_config.argument
        label = Text()
        if isinstance(node, Group):
            label.append(node.name, style=name_style)
            name_len = len(node.name)
        else:
            label.append(node.name, style=name_style)
            for arg in sorted(node.arguments, key=lambda x: (x.sort_key, x.name)):
                label.append(" ")
                label.append(f"[{arg.name.upper()}", style=arg_style)
                if self.show_types:
                    label.append(Text.from_markup(f",[{self.color_config.type_color}]{arg.arg_type.__name__}[/{self.color_config.type_color}]"))
                label.append("]", style=arg_style)
            name_len = label.cell_len
        prefix_len = depth * 4
        padding = max_start - prefix_len - name_len
        label.append(" " * padding)
        if node.help:
            label.append(" ")
            help_lines = self._wrap_help(node.help, self.max_width - (max_start + 1))
            label.append(help_lines[0], style=help_style)
            for hl in help_lines[1:]:
                label.append("\n")
                label.append(" " * (name_len + padding + 1))
                label.append(hl, style=help_style)
        return label

    def _get_option_label(self, opt: Option, max_start: int, depth: int, is_ancestor: bool) -> Text:
        option_style = "dim " + self.color_config.option if is_ancestor else self.color_config.option
        label = Text()
        flags = sorted(opt.flags, key=lambda f: (-len(f), f))
        flags_str = ", ".join(flags)
        label.append(flags_str, style=option_style)
        name_len = len(flags_str)
        if self.show_types:
            type_name = 'bool' if opt.is_flag else opt.arg_type.__name__
            label.append(Text.from_markup(f": [{self.color_config.type_color}]{type_name}[/{self.color_config.type_color}]"))
            name_len = label.cell_len
        prefix_len = depth * 4
        padding = max_start - prefix_len - name_len
        label.append(" " * padding)
        if opt.help:
            label.append(" ")
            help_lines = self._wrap_help(opt.help, self.max_width - (max_start + 1))
            label.append(help_lines[0], style=self.color_config.option_help)
            for hl in help_lines[1:]:
                label.append("\n")
                label.append(" " * (name_len + padding + 1))
                label.append(hl, style=self.color_config.option_help)
        return label

    def _add_children(self, current_tree: Tree, node: Union["Cli", Group, Command], on_path: bool, remaining_path: List[str], max_start: int, depth: int, selected_depth: int):
        is_ancestor = depth < selected_depth
        if not isinstance(node, Cli):
            opts = sorted(node.options, key=lambda x: (x.sort_key, x.flags[0]))
            for opt in opts:
                opt_label = self._get_option_label(opt, max_start, depth + 1, is_ancestor)
                current_tree.add(opt_label)
        if isinstance(node, Command):
            return
        children = sorted((node.subgroups + node.commands) if hasattr(node, 'subgroups') else [], key=lambda x: (x.sort_key, x.name))
        if on_path and remaining_path:
            next_name = remaining_path[0]
            for child in children:
                if child.name == next_name:
                    child_is_ancestor = (depth + 1) < selected_depth
                    child_label = self._get_label(child, max_start, True, depth + 1, child_is_ancestor)
                    child_tree = current_tree.add(child_label)
                    self._add_children(child_tree, child, True, remaining_path[1:], max_start, depth + 1, selected_depth)
                    break
        else:
            for child in children:
                child_label = self._get_label(child, max_start, False, depth + 1, False)
                child_tree = current_tree.add(child_label)
                self._add_children(child_tree, child, False, [], max_start, depth + 1, selected_depth)

