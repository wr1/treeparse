"""help renderer: renders CLI tree help via Rich."""

from typing import TYPE_CHECKING, List, Union
from rich.console import Console
from rich.tree import Tree
from rich.text import Text

if TYPE_CHECKING:
    from ..models.cli import cli
    from ..models.group import group
    from ..models.command import command
    from ..models.chain import chain
    from ..models.option import option


class help_renderer:
    """Renders rich tree help for a cli node."""

    def __init__(self, root_cli: "cli"):
        self._root = root_cli

    def render(self, path: List[str]):
        root_cli = self._root
        # Find the deepest valid command path
        current = root_cli
        consumed = 0
        for i, p in enumerate(path):
            if not hasattr(current, "subgroups"):
                if type(current).__name__ == "command" and consumed < len(path):
                    break
                raise ValueError(f"Path not found: {path}")
            children = current.subgroups + current.commands
            ch = next((c for c in children if c.display_name == p), None)
            if ch is None:
                raise ValueError(f"Path not found: {path}")
            current = ch
            consumed = i + 1
        effective_path = path[:consumed]
        path_str = " ".join(effective_path)
        if path_str:
            path_str += " "
        if consumed < len(path):
            path_str += "[ARGS...] "
        usage = f"[bold]Usage: {root_cli.display_name} {path_str}... [rgb(45,45,45)] (--json, -j, --help, -h)"
        console = Console(width=root_cli.max_width)
        console.print(usage)
        console.print(
            f"[{root_cli.colors.requested_help}]Description: {current.help}[/{root_cli.colors.requested_help}]"
        )
        max_start = self._compute_max_start(effective_path)
        selected_depth = len(effective_path)
        root_label = self._get_root_label(max_start, 0, True)
        tree = Tree(root_label, guide_style=root_cli.colors.guide)
        self._add_children(tree, root_cli, True, effective_path, max_start, 0, selected_depth)
        console.print(tree)

    def _compute_max_start(self, effective_path: List[str]) -> int:
        root_cli = self._root
        max_start = 0

        def collect_recurse(node, on_path: bool, remaining_path: List[str], depth: int):
            nonlocal max_start
            name_len = len(self._get_name_part(node))
            prefix_len = depth * 4
            max_start = max(max_start, prefix_len + name_len)
            opts = node.options if hasattr(node, "options") else node.effective_options
            opts_sorted = sorted(opts, key=lambda x: x.sort_key)
            for opt in opts_sorted:
                flags = sorted(opt.flags, key=lambda f: (-len(f), f))
                opt_name = ", ".join(flags)
                opt_len = len(opt_name)
                if root_cli.show_types:
                    type_name = opt.arg_type.__name__
                    opt_len += len(f": {type_name}")
                if opt.choices is not None:
                    choices_str = f" ({'|'.join(map(str, opt.choices))})"
                    opt_len += len(choices_str)
                opt_prefix = (depth + 1) * 4
                max_start = max(max_start, opt_prefix + opt_len)
            if type(node).__name__ in ("command", "chain"):
                return
            children = sorted(
                (node.subgroups + node.commands) if hasattr(node, "subgroups") else [],
                key=lambda x: x.sort_key,
            )
            if on_path and remaining_path:
                next_name = remaining_path[0]
                for child in children:
                    if child.display_name == next_name:
                        collect_recurse(child, True, remaining_path[1:], depth + 1)
                        break
            else:
                for child in children:
                    if type(child).__name__ == "group" and child.fold:
                        folded_name = f"{child.display_name} [...]"
                        name_len = len(folded_name)
                        prefix_len = (depth + 1) * 4
                        max_start = max(max_start, prefix_len + name_len)
                    else:
                        collect_recurse(child, False, [], depth + 1)

        collect_recurse(root_cli, True, effective_path, 0)
        return max_start

    def _get_name_part(self, node) -> str:
        root_cli = self._root
        args_parts = []
        args_list = (
            node.arguments if hasattr(node, "arguments") else node.effective_arguments
        )
        for arg in sorted(args_list, key=lambda x: x.sort_key):
            part = f"[{arg.name.upper()}"
            extra = []
            if root_cli.show_types:
                extra.append(arg.arg_type.__name__)
            if arg.choices is not None:
                extra.append(f"({'|'.join(map(str, arg.choices))})")
            if extra:
                part += f", {' '.join(extra)}"
            part += "]"
            args_parts.append(part)
        args_str = " ".join(args_parts)
        return f"{node.display_name} {args_str}".rstrip()

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
                lines.append(" ".join(current))
                current = [word]
                current_len = word_len
            else:
                if current:
                    current_len += 1
                current.append(word)
                current_len += word_len
        if current:
            lines.append(" ".join(current))
        return lines

    def _get_root_label(self, max_start: int, depth: int, is_ancestor: bool) -> Text:
        root_cli = self._root
        style = "dim " + root_cli.colors.app if is_ancestor else root_cli.colors.app
        help_style = (
            "dim " + root_cli.colors.normal_help
            if is_ancestor
            else root_cli.colors.normal_help
        )
        label = Text()
        label.append(root_cli.display_name, style=style)
        args_parts = []
        for arg in sorted(root_cli.arguments, key=lambda x: x.sort_key):
            part = f"[{arg.name.upper()}"
            extra = []
            if root_cli.show_types:
                extra.append(arg.arg_type.__name__)
            if arg.choices is not None:
                extra.append(f"({'|'.join(map(str, arg.choices))})")
            if extra:
                part += f", {' '.join(extra)}"
            part += "]"
            args_parts.append(part)
        args_str = " ".join(args_parts)
        if args_str:
            label.append(" ")
            label.append(
                args_str,
                style="dim " + root_cli.colors.argument if is_ancestor else root_cli.colors.argument,
            )
        name_len = label.cell_len
        prefix_len = depth * 4
        padding = max_start - prefix_len - name_len
        if root_cli.help:
            help_lines = self._wrap_help(root_cli.help, root_cli.max_width - (max_start + 1))
            if root_cli.line_connect:
                label.append(Text("─" * (padding + 1), style=root_cli.colors.connector))
                label.append(help_lines[0], style=help_style)
                for hl in help_lines[1:]:
                    label.append("\n")
                    label.append(" " * (name_len + padding + 1))
                    label.append(hl, style=help_style)
            else:
                label.append(" " * padding)
                label.append(" ")
                label.append(help_lines[0], style=help_style)
                for hl in help_lines[1:]:
                    label.append("\n")
                    label.append(" " * (name_len + padding + 1))
                    label.append(hl, style=help_style)
        else:
            label.append(" " * padding)
        return label

    def _get_label(self, node, max_start: int, on_path: bool, depth: int, is_ancestor: bool) -> Text:
        root_cli = self._root
        node_type = type(node).__name__
        base_help_style = (
            root_cli.colors.requested_help if on_path else root_cli.colors.normal_help
        )
        help_style = "dim " + base_help_style if is_ancestor else base_help_style
        name_style = (
            "dim " + root_cli.colors.group
            if is_ancestor and node_type == "group"
            else root_cli.colors.group
            if node_type == "group"
            else "dim " + root_cli.colors.command
            if is_ancestor
            else root_cli.colors.command
        )
        arg_style = (
            "dim " + root_cli.colors.argument if is_ancestor else root_cli.colors.argument
        )
        label = Text()
        label.append(node.display_name, style=name_style)
        args_list = (
            node.arguments if node_type == "group" else node.effective_arguments
        )
        args_parts = []
        for arg in sorted(args_list, key=lambda x: x.sort_key):
            part = f"[{arg.name.upper()}"
            extra = []
            if root_cli.show_types:
                extra.append(arg.arg_type.__name__)
            if arg.choices is not None:
                extra.append(f"({'|'.join(map(str, arg.choices))})")
            if extra:
                part += f", {' '.join(extra)}"
            part += "]"
            args_parts.append(part)
        args_str = " ".join(args_parts)
        if args_str:
            label.append(" ")
            label.append(args_str, style=arg_style)
        name_len = label.cell_len
        prefix_len = depth * 4
        padding = max_start - prefix_len - name_len
        if node.help:
            help_lines = self._wrap_help(node.help, root_cli.max_width - (max_start + 1))
            if root_cli.line_connect:
                label.append(Text("─" * (padding + 1), style=root_cli.colors.connector))
                label.append(help_lines[0], style=help_style)
                for hl in help_lines[1:]:
                    label.append("\n")
                    label.append(" " * (name_len + padding + 1))
                    label.append(hl, style=help_style)
            else:
                label.append(" " * padding)
                label.append(" ")
                label.append(help_lines[0], style=help_style)
                for hl in help_lines[1:]:
                    label.append("\n")
                    label.append(" " * (name_len + padding + 1))
                    label.append(hl, style=help_style)
        else:
            label.append(" " * padding)
        return label

    def _get_folded_label(self, node, max_start: int, depth: int, is_ancestor: bool) -> Text:
        root_cli = self._root
        name_style = (
            "dim " + root_cli.colors.group if is_ancestor else root_cli.colors.group
        )
        help_style = (
            "dim " + root_cli.colors.normal_help
            if is_ancestor
            else root_cli.colors.normal_help
        )
        label = Text()
        label.append(f"{node.display_name} [...]", style=name_style)
        name_len = label.cell_len
        prefix_len = depth * 4
        padding = max_start - prefix_len - name_len
        if node.help:
            help_lines = self._wrap_help(node.help, root_cli.max_width - (max_start + 1))
            if root_cli.line_connect:
                label.append(Text("─" * (padding + 1), style=root_cli.colors.connector))
                label.append(help_lines[0], style=help_style)
                for hl in help_lines[1:]:
                    label.append("\n")
                    label.append(" " * (name_len + padding + 1))
                    label.append(hl, style=help_style)
            else:
                label.append(" " * padding)
                label.append(" ")
                label.append(help_lines[0], style=help_style)
                for hl in help_lines[1:]:
                    label.append("\n")
                    label.append(" " * (name_len + padding + 1))
                    label.append(hl, style=help_style)
        else:
            label.append(" " * padding)
        return label

    def _get_option_label(self, opt, max_start: int, depth: int, is_ancestor: bool) -> Text:
        root_cli = self._root
        option_style = (
            "dim " + root_cli.colors.option if is_ancestor else root_cli.colors.option
        )
        option_help_style = (
            "dim " + root_cli.colors.option_help
            if is_ancestor
            else root_cli.colors.option_help
        )
        default_style = "bold dim white"
        label = Text()
        flags = sorted(opt.flags, key=lambda f: (-len(f), f))
        flags_str = ", ".join(flags)
        label.append(flags_str, style=option_style)
        type_part = ""
        if root_cli.show_types:
            type_name = opt.arg_type.__name__
            type_part = f": {type_name}"
        choices_part = ""
        if opt.choices is not None:
            choices_part = f" ({'|'.join(map(str, opt.choices))})"
        label.append(type_part + choices_part, style=root_cli.colors.type_color)
        name_len = label.cell_len
        prefix_len = depth * 4
        padding = max_start - prefix_len - name_len
        if opt.help:
            help_lines = self._wrap_help(opt.help, root_cli.max_width - (max_start + 1))
            if root_cli.line_connect:
                label.append(Text("─" * (padding + 1), style=root_cli.colors.connector))
                label.append(help_lines[0], style=option_help_style)
                for hl in help_lines[1:]:
                    label.append("\n")
                    label.append(" " * (name_len + padding + 1))
                    label.append(hl, style=option_help_style)
            else:
                label.append(" " * padding)
                label.append(" ")
                label.append(help_lines[0], style=option_help_style)
                for hl in help_lines[1:]:
                    label.append("\n")
                    label.append(" " * (name_len + padding + 1))
                    label.append(hl, style=option_help_style)
        else:
            label.append(" " * padding)
        if root_cli.show_defaults and opt.default is not None:
            default_str = f" (default: {opt.default})"
            if opt.help:
                label.append(
                    Text.from_markup(f"[{default_style}]{default_str}[/{default_style}]")
                )
            else:
                label.append(" ")
                label.append(
                    Text.from_markup(f"[{default_style}]{default_str}[/{default_style}]")
                )
        return label

    def _add_children(
        self,
        current_tree: Tree,
        node,
        on_path: bool,
        remaining_path: List[str],
        max_start: int,
        depth: int,
        selected_depth: int,
    ):
        is_ancestor = depth < selected_depth
        opts = node.options if hasattr(node, "options") else node.effective_options
        opts_sorted = sorted(opts, key=lambda x: x.sort_key)
        for opt in opts_sorted:
            opt_label = self._get_option_label(opt, max_start, depth + 1, is_ancestor)
            current_tree.add(opt_label)
        node_type = type(node).__name__
        if node_type in ("command", "chain"):
            return
        children = sorted(
            (node.subgroups + node.commands) if hasattr(node, "subgroups") else [],
            key=lambda x: x.sort_key,
        )
        if on_path and remaining_path:
            next_name = remaining_path[0]
            for child in children:
                if child.display_name == next_name:
                    child_is_ancestor = (depth + 1) < selected_depth
                    child_label = self._get_label(child, max_start, True, depth + 1, child_is_ancestor)
                    child_tree = current_tree.add(child_label)
                    self._add_children(
                        child_tree, child, True, remaining_path[1:], max_start, depth + 1, selected_depth
                    )
                    break
        else:
            for child in children:
                if type(child).__name__ == "group" and child.fold:
                    folded_label = self._get_folded_label(child, max_start, depth + 1, False)
                    current_tree.add(folded_label)
                else:
                    child_label = self._get_label(child, max_start, False, depth + 1, False)
                    child_tree = current_tree.add(child_label)
                    self._add_children(
                        child_tree, child, False, [], max_start, depth + 1, selected_depth
                    )
