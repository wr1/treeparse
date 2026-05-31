Output docs/assets/help.gif

# Prerequisites:
#   - uv (https://astral.sh/uv)
#   - VHS (https://github.com/charmbracelet/vhs)
#   - Monokai Remastered font installed
#   - Run from repo root after `uv sync --dev`
#   The `uv run` commands below rely on an editable install of the local treeparse source.

Set Shell "bash"
Set FontSize 13
Set Width 100
Set Height 34
Set Theme "Monokai Remastered"
Set Padding 12
Set TypingSpeed 40ms
Set PlaybackSpeed 1

# monokai theme demo
Type "uv run python examples/monokai_theme_demo.py --help"
Sleep 500ms
Enter
Sleep 3s

Type "uv run python examples/monokai_theme_demo.py build --help"
Sleep 500ms
Enter
Sleep 3s

# github theme demo
Type "uv run python examples/github_theme_demo.py --help"
Sleep 500ms
Enter
Sleep 3s

Type "uv run python examples/github_theme_demo.py pr --help"
Sleep 500ms
Enter
Sleep 4s
