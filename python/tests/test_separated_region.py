import pytest

from nagrica.game                    import Capture
from nagrica.grid.boards             import Board, LinkedBoard
from nagrica.grid.coord              import Coord
from nagrica.grid.direction          import Direction
from nagrica.grid.edge               import Edge
from nagrica.grid.vector             import Vector


@pytest.fixture
def board(board_class: type[Board]) -> Board:
    return board_class(3, 3)


def wall_off_corner(board: Board):
    """Seal (0, 0) off from the rest of the board."""
    board.place_wall(Edge(Coord(0, 0), Direction.NORTH))
    board.place_wall(Edge(Coord(0, 0), Direction.EAST))


# ---------------------------------------------------------------- Capture


def test_capture_points_and_split():
    capture = Capture(frozenset({Coord(0, 0), Coord(0, 1)}))

    assert capture.points == 2
    assert capture.split


def test_capture_without_cells():
    capture = Capture(frozenset())

    assert capture.points == 0
    assert not capture.split


# ---------------------------------------------------------------- direction order (LinkedBoard)


@pytest.mark.parametrize("offset, first", [
    (Vector( 0,  5), Direction.NORTH),
    (Vector( 3,  0), Direction.EAST),
    (Vector( 1, -4), Direction.SOUTH),
    (Vector(-2,  1), Direction.WEST),
])
def test_direction_order_prefers_goal_direction(offset: Vector[int], first: Direction):
    order = LinkedBoard._direction_order(offset)

    assert order[0]             is first
    assert order[-1]            is first.opposite
    assert sorted(order)        == sorted(Direction)


# ---------------------------------------------------------------- separated_region


def test_open_board_is_not_separated(board: Board):
    assert board.separated_region((0, 0), (2, 2)) == frozenset()


def test_start_equals_goal(board: Board):
    assert board.separated_region((1, 1), (1, 1)) == frozenset()


def test_connected_around_walls(board: Board):
    # Wall across the middle, gap on the east side:
    #   +---+---+---+
    #   |           |
    #   +---+---+   +
    #   |           |
    #   +   +   +   +
    #   |           |
    #   +---+---+---+
    board.place_wall(Edge(Coord(0, 1), Direction.NORTH))
    board.place_wall(Edge(Coord(1, 1), Direction.NORTH))

    assert board.separated_region((0, 0), (0, 2)) == frozenset()


def test_region_from_sealed_corner(board: Board):
    wall_off_corner(board)

    assert board.separated_region((0, 0), (2, 2)) == {Coord(0, 0)}


def test_region_is_one_side_of_the_split(board: Board):
    # Either side may be returned, choosing what to capture is up to the game
    wall_off_corner(board)

    corner  = {Coord(0, 0)}
    rest    = {Coord(x, y) for x in range(3) for y in range(3)} - corner

    assert board.separated_region((2, 2), (0, 0)) in (corner, rest)
    assert board.separated_region((0, 0), (2, 2)) in (corner, rest)


def test_region_can_be_repeated(board: Board):
    assert board.separated_region((0, 0), (2, 2)) == frozenset()

    wall_off_corner(board)

    assert board.separated_region((0, 0), (2, 2)) == {Coord(0, 0)}
