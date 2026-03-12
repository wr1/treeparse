from treeparse import cli, command


def hello():
    print("Treeparse CLI")


app = cli(
    name="treeparse",
    help="Treeparse framework CLI",
    commands=[command(name="hello", callback=hello)],
)


def main():
    app.run()
