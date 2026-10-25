from collections.abc        import Mapping


from nagrica.grid           import Board, Coord, Direction



def render_board(
    board:          Board,
    labels:         Mapping[Coord, str] | None  = None,
    cell_width:     int                         = 3
) -> str:
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


    lines: list[str] = []

    # NORTH is +y, so print the highest row first
    for y in reversed(range(board.height)):
        lines.append(_wall_line(y, Direction.NORTH))
        lines.append(_content_line(y))

    lines.append(_wall_line(0, Direction.SOUTH))

    return "\n".join(lines)