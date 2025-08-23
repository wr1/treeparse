import sys
import logging
from pathlib import Path
from typing import List

sys.path.append(str(Path(__file__).parent.parent / "src"))
from treeparse import cli, group, command, argument, option

logging.basicConfig(level=logging.INFO)


def info(verbose: bool = False):
    logging.info("CLI Information")
    if verbose:
        logging.info("Detailed mode enabled.")


def add_user(name: str, email: str = None):
    logging.info(f"Adding user: {name}")
    if email:
        logging.info(f"Email: {email}")


def list_users():
    logging.info("Listing all users...")


def set_role(
    role: str,
    user_id: str = None,
    reason: str = None,
    user_id_option: int = None,
    reason_option: str = None,
):
    user_id = (
        user_id_option if user_id_option is not None else (user_id or "unspecified")
    )
    reason = reason_option if reason_option is not None else reason
    logging.info(f"Setting role {role} for user ID {user_id}")
    if reason:
        logging.info(f"Reason: {reason}")


def remove_role(role: str, user_id: str):
    logging.info(f"Removing role {role} for user {user_id}")


def add_permission(user_id: str, permission: str):
    logging.info(f"Adding permission {permission} for user {user_id}")


def echo(words: List[str]):
    logging.info("Echo: " + " ".join(words))


def tag(tags: List[str]):
    logging.info(f"Tags: {tags}")


app = cli(
    name="demo.py",
    help="This CLI provides commands to handle various tasks with subcommands for specific actions.",
    max_width=135,
    show_types=True,
)

info_cmd = command(
    name="info",
    help="Display CLI information.",
    callback=info,
    options=[
        option(
            flags=["--verbose", "-v"],
            is_flag=True,
            help="Show detailed information.",
            sort_key=0,
        ),
    ],
)
app.commands.append(info_cmd)

project = group(name="project", help="Manage project-related operations.")
app.subgroups.append(project)

user = group(name="user", help="Manage user-related operations.")
app.subgroups.append(user)

add_cmd = command(
    name="add",
    help="Add a new user to the system.",
    callback=add_user,
    arguments=[
        argument(name="name", arg_type=str, sort_key=0),
    ],
    options=[
        option(
            flags=["--email", "-e"],
            help="Email address of the user",
            arg_type=str,
            sort_key=0,
        ),
    ],
)
user.commands.append(add_cmd)

list_cmd = command(
    name="list",
    help="List all users in the system.",
    callback=list_users,
)
user.commands.append(list_cmd)

manage = group(name="manage", help="Manage user settings and permissions.")
user.subgroups.append(manage)

set_role_cmd = command(
    name="set-role",
    help="Set a role for a user.",
    callback=set_role,
    arguments=[
        argument(name="role", arg_type=str, nargs="?", default=None, sort_key=0),
        argument(name="user_id", arg_type=str, nargs="?", default=None, sort_key=1),
        argument(name="reason", arg_type=str, nargs="?", default=None, sort_key=2),
    ],
    options=[
        option(
            flags=["--user-id", "-u"],
            dest="user_id_option",
            help="User ID to set role for (unspecified if not provided), where the help is really really long to test the wrapping of the lines in the CLI even if the terminal width is really wide it still tests it because it is just so very very long.",
            arg_type=int,
            sort_key=0,
        ),
        option(
            flags=["--reason", "-r"],
            dest="reason_option",
            help="Reason for setting the role",
            arg_type=str,
            sort_key=1,
        ),
    ],
)
manage.commands.append(set_role_cmd)

remove_role_cmd = command(
    name="remove-role",
    help="Remove a role from a user.",
    callback=remove_role,
    arguments=[
        argument(name="role", arg_type=str, sort_key=0),
        argument(name="user_id", arg_type=str, sort_key=1),
    ],
)
manage.commands.append(remove_role_cmd)

permissions = group(name="permissions", help="Manage user permissions.")
manage.subgroups.append(permissions)

set_permissions = group(name="set", help="Manage user permissions.")
permissions.subgroups.append(set_permissions)

add_perm_cmd = command(
    name="add",
    help="Add a permission for a user.",
    callback=add_permission,
    arguments=[
        argument(name="user_id", arg_type=str, sort_key=0),
        argument(name="permission", arg_type=str, sort_key=1),
    ],
)
set_permissions.commands.append(add_perm_cmd)

echo_cmd = command(
    name="echo",
    help="Echo the provided words.",
    callback=echo,
    arguments=[
        argument(name="words", nargs="*", arg_type=str, sort_key=0),
    ],
)
app.commands.append(echo_cmd)

tag_cmd = command(
    name="tag",
    help="Add tags.",
    callback=tag,
    options=[
        option(
            flags=["--tags", "-t"],
            nargs="+",
            arg_type=str,
            help="Tags to add",
            sort_key=0,
        ),
    ],
)
app.commands.append(tag_cmd)


def main():
    app.run()


if __name__ == "__main__":
    main()
