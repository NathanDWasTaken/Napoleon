"""
Behaviour every `Board` implementation must share. Runs against each class in `BOARDS`.
"""
import pytest

from nagrica.grid.boards         import Board
from nagrica.grid.coord          import Coord
from nagrica.grid.direction      import Direction
from nagrica.grid.exceptions     import CellOutOfBounds


N, E, S, W = Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST

ALL_COORDS = {Coord(x, y) for y in range(2) for x in range(3)}


@pytest.fixture
def board(board_class: type[Board]) -> Board:
    # Deliberately not square, so height and width can't be mixed up
    return board_class(height=2, width=3)


# ---------------------------------------------------------------- structure


def test_dimensions(board: Board):
    assert board.height == 2
    assert board.width  == 3


def test_every_cell_starts_in_play(board: Board):
    assert set(board.in_play)   == ALL_COORDS
    assert board.num_in_play    == 6

    for coord in ALL_COORDS:
        assert board.is_in_play(coord)


def test_in_play_yields_coords(board: Board):
    assert all(type(coord) is Coord for coord in board.in_play)


def test_every_cell_starts_unowned(board: Board):
    for coord in ALL_COORDS:
        assert board.owner(coord) == -1


@pytest.mark.parametrize("coord, valid", [
    ((0,  0), True),
    ((2,  1), True),
    ((3,  0), False),
    ((0,  2), False),
    ((-1, 0), False),
    ((0, -1), False),
])
def test_coord_is_valid(board: Board, coord: tuple[int, int], valid: bool):
    assert board.coord_is_valid(coord) == valid


def test_every_in_bounds_neighbour_connects(board: Board):
    for coord in ALL_COORDS:
        for direction in Direction:
            exists = board.coord_is_valid(coord.to_neighbor(direction))

            assert board.connects(coord, direction) == exists, f"{coord} {direction.name}"


@pytest.mark.parametrize("coord, count", [
    (Coord(0, 0), 2),   # corner
    (Coord(1, 0), 3),   # edge
    (Coord(1, 1), 4),   # interior
])
def test_connection_counts(board_class: type[Board], coord: Coord, count: int):
    board = board_class(3, 3)

    assert sum(board.connects(coord, direction) for direction in Direction) == count


def test_accepts_tuple_coords(board: Board):
    assert board.connects((0, 0), E)
    assert board.is_in_play((2, 1))
    assert board.owner((2, 1)) == -1


# ---------------------------------------------------------------- walls


def test_place_wall_disconnects_both_sides(board: Board):
    board.place_wall((0, 0), E)

    assert not board.connects((0, 0), E)
    assert not board.connects((1, 0), W)


def test_place_wall_leaves_other_connections(board: Board):
    board.place_wall((0, 0), E)

    assert board.connects((0, 0), N)
    assert board.connects((1, 0), E)
    assert board.connects((1, 0), N)


def test_place_wall_leaves_play_area(board: Board):
    board.place_wall((0, 0), E)

    assert set(board.in_play) == ALL_COORDS


def test_place_wall_off_board_raises(board: Board):
    with pytest.raises(CellOutOfBounds):
        board.place_wall((0, 0), S)


def test_remove_wall_restores_connection(board: Board):
    board.place_wall((0, 0), E)
    board.remove_wall((0, 0), E)

    assert board.connects((0, 0), E)
    assert board.connects((1, 0), W)


def test_remove_wall_from_other_side(board: Board):
    board.place_wall((0, 0), E)
    board.remove_wall((1, 0), W)

    assert board.connects((0, 0), E)
    assert board.connects((1, 0), W)


def test_remove_wall_off_board_raises(board: Board):
    with pytest.raises(CellOutOfBounds):
        board.remove_wall((0, 0), S)


# ---------------------------------------------------------------- captures


def test_capture_sets_owner_and_removes_from_play(board: Board):
    board.capture(1, {Coord(0, 0), Coord(0, 1)})

    assert board.owner((0, 0))      == 1
    assert board.owner((0, 1))      == 1
    assert not board.is_in_play((0, 0))
    assert not board.is_in_play((0, 1))
    assert board.num_in_play        == 4


def test_capture_leaves_other_cells(board: Board):
    board.capture(1, {Coord(0, 0)})

    assert board.owner((1, 0)) == -1
    assert set(board.in_play)  == ALL_COORDS - {Coord(0, 0)}


def test_capture_accepts_generator(board: Board):
    board.capture(1, (coord for coord in [Coord(0, 0), Coord(1, 0)]))

    assert board.owner((0, 0))  == 1
    assert board.owner((1, 0))  == 1
    assert board.num_in_play    == 4


def test_release_undoes_capture(board: Board):
    board.capture(1, {Coord(0, 0), Coord(0, 1)})
    board.release({Coord(0, 0), Coord(0, 1)})

    assert board.owner((0, 0))  == -1
    assert board.owner((0, 1))  == -1
    assert set(board.in_play)   == ALL_COORDS
