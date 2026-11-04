from collections.abc        import Mapping


from nagrica.grid           import Board, Coord, Direction, Edge

from .notation              import column_name



def render_board(
    board:          Board,
    labels:         Mapping[Coord, str] | None  = None,
    cell_width:     int                         = 3,
    axes:           bool                        = False,
    owners:         Mapping[Coord, int] | None  = None,
    notation:       bool                        = False,
) -> str:
    """
    Draw the board as ASCII art. With `axes`, rows are numbered by y on the
    left and right and columns by x above and below, so players can read off
    coordinates. With `notation` as well, the axes use the names of game records
    instead: columns a, b, c, ... and rows from 1. `owners` maps captured cells
    to the seat that owns them.
    """
    labels = labels or {}
    owners = owners or {}


    def _column_label(x: int) -> str:
        return column_name(x) if notation else str(x)

    def _row_label(y: int) -> str:
        return str(y + 1) if notation else str(y)


    def _wall_line(y: int, direction: Direction) -> str:
        line = "+"

        for x in range(board.width):
            coord   = Coord(x, y)
            line   += (" " if board.connects(Edge(coord, direction)) else "-") * cell_width
            line   += "+"

        return line


    def _content_line(y: int) -> str:
        line = "|"

        for x in range(board.width):
            coord   = Coord(x, y)
            owner   = owners.get(coord)
            content = labels.get(coord) or ("" if owner is None else str(owner))

            line   += content.center(cell_width)
            line   += " " if board.connects(Edge(coord, Direction.EAST)) else "|"

        return line


    def _x_axis_line() -> str:
        # Offset by the left border, so each number lines up with its cell
        line = " "

        for x in range(board.width):
            line   += _column_label(x).center(cell_width)
            line   += " "

        return line.rstrip()


    # Room for the widest y label plus a space, or nothing without axes
    label_width = len(_row_label(board.height - 1)) if axes else 0
    margin      = " " * (label_width + 1) if axes else ""

    lines: list[str] = []

    if axes:
        lines.append(margin + _x_axis_line())

    # NORTH is +y, so print the highest row first
    for y in reversed(range(board.height)):
        left_label  = f"{_row_label(y):>{label_width}} " if axes else ""
        right_label = f" {_row_label(y)}"                if axes else ""

        lines.append(margin     + _wall_line(y, Direction.NORTH))
        lines.append(left_label + _content_line(y) + right_label)

    lines.append(margin + _wall_line(0, Direction.SOUTH))

    if axes:
        lines.append(margin + _x_axis_line())

    return "\n".join(lines)