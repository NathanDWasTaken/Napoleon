from collections.abc        import Mapping


from nagrica.grid           import Board, Coord, Direction



def render_board(
    board:          Board,
    labels:         Mapping[Coord, str] | None  = None,
    cell_width:     int                         = 3,
    axes:           bool                        = False
) -> str:
    """
    Draw the board as ASCII art. With `axes`, rows are numbered by y on the
    left and right and columns by x above and below, so players can read off
    coordinates.
    """
    labels = labels or {}


    def _wall_line(y: int, direction: Direction) -> str:
        line = "+"

        for x in range(board.width):
            coord   = Coord(x, y)
            line   += (" " if board.connects(coord, direction) else "-") * cell_width
            line   += "+"

        return line


    def _content_line(y: int) -> str:
        line = "|"

        for x in range(board.width):
            coord   = Coord(x, y)
            owner   = board.owner(coord)
            content = labels.get(coord) or ("" if owner == -1 else str(owner))

            line   += content.center(cell_width)
            line   += " " if board.connects(coord, Direction.EAST) else "|"

        return line


    def _x_axis_line() -> str:
        # Offset by the left border, so each number lines up with its cell
        line = " "

        for x in range(board.width):
            line   += str(x).center(cell_width)
            line   += " "

        return line.rstrip()


    # Room for the widest y label plus a space, or nothing without axes
    label_width = len(str(board.height - 1)) if axes else 0
    margin      = " " * (label_width + 1) if axes else ""

    lines: list[str] = []

    if axes:
        lines.append(margin + _x_axis_line())

    # NORTH is +y, so print the highest row first
    for y in reversed(range(board.height)):
        left_label  = f"{y:>{label_width}} " if axes else ""
        right_label = f" {y}"                if axes else ""

        lines.append(margin     + _wall_line(y, Direction.NORTH))
        lines.append(left_label + _content_line(y) + right_label)

    lines.append(margin + _wall_line(0, Direction.SOUTH))

    if axes:
        lines.append(margin + _x_axis_line())

    return "\n".join(lines)