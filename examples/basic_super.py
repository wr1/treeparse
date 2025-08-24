# import sys
# from pathlib import Path

# sys.path.append(str(Path(__file__).parent))

from basic import app as basic_app
from demo import app as demo_app
from list_demo import app as list_demo_app
from treeparse import cli

super_app = cli(
    name="basic_super.py",
    help="A super CLI that includes the basic CLI as a sub-CLI.",
    subgroups=[basic_app, demo_app, list_demo_app],
)


def main():
    super_app.run()


if __name__ == "__main__":
    main()
