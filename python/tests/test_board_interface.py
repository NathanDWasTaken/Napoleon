"""
Behaviour every `Board` implementation must share. Runs against each class in `BOARDS`.
"""
from random         import Random

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


# ---------------------------------------------------------------- copy


def snapshot(board: Board) -> tuple:
    """Everything observable about a board, through the public interface only."""
    coords = [Coord(x, y) for y in range(board.height) for x in range(board.width)]

    return (
        board.height,
        board.width,
        frozenset((coord, direction) for coord in coords for direction in Direction if board.connects(coord, direction)),
        {coord: board.owner(coord) for coord in coords},
        frozenset(board.in_play),
    )


def played_board(board_class: type[Board], seed: int) -> Board:
    """A 4x5 board with some random walls and captures on it."""
    rng     = Random(seed)
    board   = board_class(4, 5)
    coords  = [Coord(x, y) for y in range(4) for x in range(5)]

    for coord in rng.sample(coords, 8):
        direction = rng.choice([N, E])

        if board.connects(coord, direction):
            board.place_wall(coord, direction)

    board.capture(rng.randrange(3), rng.sample(coords, 3))

    return board


def test_copy_is_same_class(board: Board):
    assert type(board.copy()) is type(board)


def test_copy_of_fresh_board_matches(board: Board):
    assert snapshot(board.copy()) == snapshot(board)


@pytest.mark.parametrize("seed", range(5))
def test_copy_matches_played_board(board_class: type[Board], seed: int):
    board = played_board(board_class, seed)

    assert snapshot(board.copy()) == snapshot(board)


@pytest.mark.parametrize("seed", range(3))
def test_copying_leaves_original_unchanged(board_class: type[Board], seed: int):
    board   = played_board(board_class, seed)
    before  = snapshot(board)

    board.copy()

    assert snapshot(board) == before


def test_copy_of_copy_matches(board_class: type[Board]):
    board = played_board(board_class, 0)

    assert snapshot(board.copy().copy()) == snapshot(board)


def test_changing_copy_leaves_original(board: Board):
    before  = snapshot(board)
    clone   = board.copy()

    clone.place_wall((0, 0), E)
    clone.capture(1, {Coord(2, 1)})

    assert snapshot(board) == before


def test_changing_original_leaves_copy(board: Board):
    clone   = board.copy()
    before  = snapshot(clone)

    board.place_wall((0, 0), E)
    board.capture(1, {Coord(2, 1)})

    assert snapshot(clone) == before


def test_undoing_on_copy_leaves_original(board: Board):
    board.place_wall((0, 0), E)
    board.capture(1, {Coord(2, 1)})

    before  = snapshot(board)
    clone   = board.copy()

    clone.remove_wall((0, 0), E)
    clone.release({Coord(2, 1)})

    assert snapshot(board) == before
