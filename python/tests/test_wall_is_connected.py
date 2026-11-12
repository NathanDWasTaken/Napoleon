import itertools
import random

import pytest

from nagrica.grid.boards    import BitBoard
from nagrica.grid.coord     import Coord
from nagrica.grid.direction import Direction
from nagrica.grid.edge      import Edge


Point = tuple[int, int]


def segment(edge: Edge) -> tuple[Point, Point]:
    """Grid-point endpoints of a wall; cell (x, y) spans points (x, y)..(x+1, y+1)."""
    x, y = edge.coord
    if edge.direction == Direction.NORTH:
        return (x, y + 1), (x + 1, y + 1)
    return (x + 1, y), (x + 1, y + 1)


def all_edges(board: BitBoard) -> list[Edge]:
    return [
        Edge(Coord(x, y), d)
        for y in range(board.height) for x in range(board.width)
        for d in (Direction.NORTH, Direction.EAST)
        if board.edge_is_valid(Edge(Coord(x, y), d))
    ]


def on_border(p: Point, board: BitBoard) -> bool:
    return p[0] in (0, board.width) or p[1] in (0, board.height)


def expected(board: BitBoard, wall: Edge, others: list[Edge]) -> bool:
    anchors = {p for e in others for p in segment(e)}
    return all(on_border(p, board) or p in anchors for p in segment(wall))


@pytest.mark.parametrize("height, width", [(3, 3), (4, 4), (3, 5), (5, 3)])
def test_wall_is_connected_matches_oracle(height: int, width: int):
    rng     = random.Random(0)
    base    = BitBoard(height, width)
    edges   = all_edges(base)

    for _ in range(300):
        placed = rng.sample(edges, rng.randint(0, len(edges) // 2))

        for wall in placed:
            board = BitBoard(height, width)
            for e in placed:
                board.place_wall(e)

            others  = [e for e in placed if e != wall]
            start   = wall.coord
            end     = wall.other

            want = expected(board, wall, others)

            for a, b in ((start, end), (end, start)):
                assert board._wall_is_connected(a, b) == want, (
                    f"{height}x{width} wall={wall} from={a} to={b} placed={placed}"
                )
