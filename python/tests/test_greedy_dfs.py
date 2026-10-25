import pytest

from nagrica.capture.capture         import Capture
from nagrica.capture.greedy_dfs      import GreedyDFS
from nagrica.grid.board              import Board
from nagrica.grid.coord              import Coord
from nagrica.grid.direction          import Direction
from nagrica.grid.vector             import Vector


@pytest.fixture
def board() -> Board:
    return Board(3, 3)


def wall_off_corner(board: Board):
    """Seal (0, 0) off from the rest of the board."""
    board.place_wall((0, 0), Direction.NORTH)
    board.place_wall((0, 0), Direction.EAST)


# ---------------------------------------------------------------- Result


def test_result_points_and_split():
    result = Capture(frozenset({Coord(0, 0), Coord(0, 1)}))

    assert result.points == 2
    assert result.split


def test_result_without_capture():
    result = Capture(frozenset())

    assert result.points == 0
    assert not result.split


# ---------------------------------------------------------------- direction order


@pytest.mark.parametrize("offset, first", [
    (Vector( 0,  5), Direction.NORTH),
    (Vector( 3,  0), Direction.EAST),
    (Vector( 1, -4), Direction.SOUTH),
    (Vector(-2,  1), Direction.WEST),
])
def test_direction_order_prefers_goal_direction(board: Board, offset: Vector[int], first: Direction):
    order = GreedyDFS(board)._direction_order(offset)

    assert order[0]             is first
    assert order[-1]            is first.opposite
    assert sorted(order)        == sorted(Direction)


# ---------------------------------------------------------------- run


def test_open_board_is_reachable(board: Board):
    result = GreedyDFS(board).run((0, 0), (2, 2))

    assert not result.split
    assert result.coords  == frozenset()


def test_start_equals_goal(board: Board):
    result = GreedyDFS(board).run((1, 1), (1, 1))

    assert not result.split


def test_reachable_around_walls(board: Board):
    # Wall across the middle, gap on the east side:
    #   +---+---+---+
    #   |           |
    #   +---+---+   +
    #   |           |
    #   +   +   +   +
    #   |           |
    #   +---+---+---+
    board.place_wall((0, 1), Direction.NORTH)
    board.place_wall((1, 1), Direction.NORTH)

    assert not GreedyDFS(board).run((0, 0), (0, 2)).split


def test_unreachable_from_sealed_corner(board: Board):
    wall_off_corner(board)

    result = GreedyDFS(board).run((0, 0), (2, 2))

    assert result.split
    assert result.coords  == {Coord(0, 0)}


def test_run_can_be_repeated(board: Board):
    dfs = GreedyDFS(board)

    assert not dfs.run((0, 0), (2, 2)).split

    wall_off_corner(board)

    assert dfs.run((0, 0), (2, 2)).split
