import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))
import click
from treeparse import Cli, Group, Command, Argument, Option


def info(args):
    click.echo("CLI Information")
    if args.verbose:
        click.echo("Detailed mode enabled.")


def add_user(args):
    click.echo(f"Adding user: {args.name}")
    if args.email:
        click.echo(f"Email: {args.email}")


def list_users(args):
    click.echo("Listing all users...")


def set_role(args):
    user_id = (
        args.user_id_option
        if args.user_id_option is not None
        else (args.user_id or "unspecified")
    )
    reason = args.reason_option if args.reason_option is not None else args.reason
    click.echo(f"Setting role {args.role} for user ID {user_id}")
    if reason:
        click.echo(f"Reason: {reason}")


def remove_role(args):
    click.echo(f"Removing role {args.role} for user {args.user_id}")


def add_permission(args):
    click.echo(f"Adding permission {args.permission} for user {args.user_id}")


cli = Cli(
    name="demo.py",
    help="This CLI provides commands to handle various tasks with subcommands for specific actions.",
    max_width=120,
)

info_cmd = Command(
    name="info",
    help="Display CLI information.",
    callback=info,
    options=[
        Option(
            flags=["--verbose", "-v"], is_flag=True, help="Show detailed information."
        ),
    ],
)
cli.commands.append(info_cmd)

project = Group(name="project", help="Manage project-related operations.")
cli.subgroups.append(project)

user = Group(name="user", help="Manage user-related operations.")
cli.subgroups.append(user)

add_cmd = Command(
    name="add",
    help="Add a new user to the system.",
    callback=add_user,
    arguments=[
        Argument(name="name", arg_type=str),
    ],
    options=[
        Option(flags=["--email", "-e"], help="Email address of the user", arg_type=str),
    ],
)
user.commands.append(add_cmd)

list_cmd = Command(
    name="list",
    help="List all users in the system.",
    callback=list_users,
)
user.commands.append(list_cmd)

manage = Group(name="manage", help="Manage user settings and permissions.")
user.subgroups.append(manage)

set_role_cmd = Command(
    name="set-role",
    help="Set a role for a user.",
    callback=set_role,
    arguments=[
        Argument(name="role", arg_type=str),
        Argument(name="user_id", arg_type=str, nargs="?", default=None),
        Argument(name="reason", arg_type=str, nargs="?", default=None),
    ],
    options=[
        Option(
            flags=["--user-id", "-u"],
            dest="user_id_option",
            help="User ID to set role for (unspecified if not provided), where the help is really really long to test the wrapping of the lines in the CLI even if the terminal width is really wide it still tests it because it is just so very very long.",
            arg_type=str,
        ),
        Option(
            flags=["--reason", "-r"],
            dest="reason_option",
            help="Reason for setting the role",
            arg_type=str,
        ),
    ],
)
manage.commands.append(set_role_cmd)

remove_role_cmd = Command(
    name="remove-role",
    help="Remove a role from a user.",
    callback=remove_role,
    arguments=[
        Argument(name="role", arg_type=str),
        Argument(name="user_id", arg_type=str),
    ],
)
manage.commands.append(remove_role_cmd)

permissions = Group(name="permissions", help="Manage user permissions.")
manage.subgroups.append(permissions)

set_permissions = Group(name="set", help="Manage user permissions.")
permissions.subgroups.append(set_permissions)

add_perm_cmd = Command(
    name="add",
    help="Add a permission for a user.",
    callback=add_permission,
    arguments=[
        Argument(name="user_id", arg_type=str),
        Argument(name="permission", arg_type=str),
    ],
)
set_permissions.commands.append(add_perm_cmd)


def main():
    cli.run()


if __name__ == "__main__":
    main()
