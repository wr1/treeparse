"""Demo of the GITHUB color theme.

Run:
    python examples/github_theme_demo.py --help
    python examples/github_theme_demo.py repo --help
    python examples/github_theme_demo.py pr --help
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))
from treeparse import argument, cli, command, group, option

# --- callbacks ---


def clone(url: str, depth: int):
    print(f"Cloning {url} (depth={depth})")


def status(short: bool, branch: bool):
    print(f"Status short={short} branch={branch}")


def commit(message: str, amend: bool):
    print(f"Committing: {message!r} amend={amend}")


def push(remote: str, force: bool):
    print(f"Pushing to {remote} force={force}")


def pr_create(title: str, draft: bool):
    print(f"Creating PR: {title!r} draft={draft}")


def pr_list(state: str):
    print(f"Listing PRs state={state!r}")


def pr_merge(number: int, squash: bool):
    print(f"Merging PR #{number} squash={squash}")


def issue_create(title: str, label: str):
    print(f"Opening issue: {title!r} label={label!r}")


def issue_list(state: str, assignee: str):
    print(f"Issues state={state!r} assignee={assignee!r}")


# --- structure ---

repo = group(name="repo", help="Repository operations.")
repo.commands.append(
    command(
        name="clone",
        help="Clone a remote repository.",
        callback=clone,
        arguments=[argument(name="url", arg_type=str, help="Repository URL")],
        options=[option(flags=["--depth", "-d"], arg_type=int, default=1, help="Clone depth")],
    )
)
repo.commands.append(
    command(
        name="status",
        help="Show working tree status.",
        callback=status,
        options=[
            option(flags=["--short", "-s"], arg_type=bool, default=False, help="Short format"),
            option(flags=["--branch", "-b"], arg_type=bool, default=False, help="Show branch info"),
        ],
    )
)
repo.commands.append(
    command(
        name="commit",
        help="Record changes to the repository.",
        callback=commit,
        options=[
            option(flags=["--message", "-m"], arg_type=str, default="chore: update", help="Commit message"),
            option(flags=["--amend"], arg_type=bool, default=False, help="Amend the last commit"),
        ],
    )
)
repo.commands.append(
    command(
        name="push",
        help="Push commits to a remote.",
        callback=push,
        options=[
            option(flags=["--remote", "-r"], arg_type=str, default="origin", help="Remote name"),
            option(flags=["--force", "-f"], arg_type=bool, default=False, help="Force push"),
        ],
    )
)

pr = group(name="pr", help="Pull request management.")
pr.commands.append(
    command(
        name="create",
        help="Open a new pull request.",
        callback=pr_create,
        options=[
            option(flags=["--title", "-t"], arg_type=str, default="", help="PR title"),
            option(flags=["--draft"], arg_type=bool, default=False, help="Mark as draft"),
        ],
    )
)
pr.commands.append(
    command(
        name="list",
        help="List pull requests.",
        callback=pr_list,
        options=[
            option(
                flags=["--state"],
                arg_type=str,
                default="open",
                choices=["open", "closed", "merged"],
                help="Filter by state",
            )
        ],
    )
)
pr.commands.append(
    command(
        name="merge",
        help="Merge a pull request.",
        callback=pr_merge,
        arguments=[argument(name="number", arg_type=int, help="PR number")],
        options=[option(flags=["--squash"], arg_type=bool, default=False, help="Squash commits on merge")],
    )
)

issues = group(name="issue", help="Issue tracker.")
issues.commands.append(
    command(
        name="create",
        help="Open a new issue.",
        callback=issue_create,
        options=[
            option(flags=["--title", "-t"], arg_type=str, default="", help="Issue title"),
            option(flags=["--label", "-l"], arg_type=str, default="", help="Label to apply"),
        ],
    )
)
issues.commands.append(
    command(
        name="list",
        help="List issues.",
        callback=issue_list,
        options=[
            option(flags=["--state"], arg_type=str, default="open", choices=["open", "closed"], help="Filter by state"),
            option(flags=["--assignee"], arg_type=str, default="", help="Filter by assignee"),
        ],
    )
)

app = cli(
    name="gh",
    help="GitHub CLI — manage repos, pull requests, and issues from your terminal.",
    theme="github",
    show_types=True,
    show_defaults=True,
    line_connect=True,
    max_width=110,
    subgroups=[repo, pr, issues],
)


def main():
    app.run()


if __name__ == "__main__":
    main()
