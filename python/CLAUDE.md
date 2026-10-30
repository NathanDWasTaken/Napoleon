# Purpose
Personal learning project to improve as a programmer. I want to write the core
parts myself, so do not do that work for me.

## Core logic: hands off
Core logic is everything in `src/nagrica/` except:
- `src/nagrica/__main__.py`
- `src/nagrica/cli.py`
- `src/nagrica/ui/`

Rules for core logic:
- Never write or edit core files.
- You may explain concepts and general approaches when I ask.
- Do not mention bugs or mistakes you notice in core logic. Stay silent about them.
- If I ask about a bug, only give hints that point me in the right direction.
  Do not give the fix or the exact cause unless I say:
  "Figure it out for me because I can't".

## Free to edit without asking
Everything that is not core logic, for example:
- Tests (`tests/`): writing and maintaining them
- CLI and entry points (`__main__.py`, `cli.py`)
- UI (`ui/`)
- Tooling and config (`pyproject.toml`, uv, `arena/`, scripts)

## Failing tests
If a test fails because of a core logic bug, tell me the test fails and that
the problem is not in the test itself. Do not say what or where the bug is.
