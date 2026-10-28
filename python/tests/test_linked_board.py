"""
Internals specific to `LinkedBoard`. Shared board behaviour lives in `test_board_interface.py`.
"""
import pytest

from nagrica.grid.boards         import LinkedBoard
from nagrica.grid.coord          import Coord
from nagrica.grid.direction      import Direction


ALL_COORDS = {Coord(x, y) for y in range(2) for x in range(3)}


@pytest.fixture
def board() -> LinkedBoard:
    return LinkedBoard(height=2, width=3)


def test_neighbours_are_linked_both_ways(board: LinkedBoard):
    for coord in ALL_COORDS:
        cell = board[coord]

        for direction, neighbour in cell.connections.items():
            assert neighbour.coord == coord.to_neighbor(direction)
            assert neighbour.connections[direction.opposite] is cell


def test_getitem(board: LinkedBoard):
    assert board[Coord(2, 1)].coord == Coord(2, 1)

    with pytest.raises(KeyError):
        board[Coord(5, 5)]


def test_getitem_accepts_tuple(board: LinkedBoard):
    assert board[(2, 1)] is board[Coord(2, 1)]


def test_contains_accepts_tuple(board: LinkedBoard):
    assert (2, 1)     in board
    assert (5, 5) not in board


def test_contains_includes_captured_cells(board: LinkedBoard):
    # `in` means "on the board", not "in play"
    board.capture(0, {Coord(0, 0)})

    assert Coord(0, 0) in board


def test_place_wall_unlinks_cells(board: LinkedBoard):
    board.place_wall((0, 0), Direction.EAST)

    assert Direction.EAST not in board[(0, 0)].connections
    assert Direction.WEST not in board[(1, 0)].connections


def test_remove_wall_relinks_same_cells(board: LinkedBoard):
    board.place_wall((0, 0), Direction.EAST)
    board.remove_wall((0, 0), Direction.EAST)

    assert board[(0, 0)].walk(Direction.EAST) is board[(1, 0)]
    assert board[(1, 0)].walk(Direction.WEST) is board[(0, 0)]


def test_capture_sets_cell_owned(board: LinkedBoard):
    board.capture(2, {Coord(1, 1)})

    assert board[(1, 1)].owned == 2


# ---------------------------------------------------------------- copy


def test_copy_shares_no_cells(board: LinkedBoard):
    clone = board.copy()

    for coord in ALL_COORDS:
        assert clone[coord] is not board[coord]


def test_copy_links_its_own_cells(board: LinkedBoard):
    clone = board.copy()

    for coord in ALL_COORDS:
        for direction, neighbour in clone[coord].connections.items():
            assert neighbour is clone[coord.to_neighbor(direction)]


def test_copy_does_not_share_in_play_set(board: LinkedBoard):
    clone = board.copy()

    assert clone._in_play is not board._in_play
