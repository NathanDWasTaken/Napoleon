from collections.abc    import Mapping
from typing             import TYPE_CHECKING

from .direction         import Direction
from .coord             import Coord

if TYPE_CHECKING:
    from .board         import Board


def render_board(
    board:              Board,
    labels:             Mapping[Coord, str] | None  = None,
    cell_width:         int                         = 3
) -> str:
    labels = labels or {}


    def _wall_line(y: int, direction: Direction) -> str:
        line = "+"

        for x in range(board.width):
            cell    = board[Coord(x, y)]
            line   += (" " if direction in cell.connections else "-") * cell_width
            line   += "+"

        return line


    def _content_line(y: int) -> str:
        line = "|"

        for x in range(board.width):
            cell    = board[Coord(x, y)]
            content = labels.get(cell.coord) or ("" if cell.owned == -1 else str(cell.owned))

            line   += content.center(cell_width)
            line   += " " if Direction.EAST in cell.connections else "|"

        return line


    lines: list[str] = []

    # NORTH is +y, so print the highest row first
    for y in reversed(range(board.height)):
        lines.append(_wall_line(y, Direction.NORTH))
        lines.append(_content_line(y))

    lines.append(_wall_line(0, Direction.SOUTH))

    return "\n".join(lines)
