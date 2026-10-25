import pytest

from nagrica.grid.board          import Board
from nagrica.grid.cell           import Cell
from nagrica.grid.coord          import Coord
from nagrica.grid.direction      import Direction
from nagrica.grid.exceptions     import CellOutOfBounds
from nagrica.grid.render         import render_board


@pytest.fixture
def board() -> Board:
    # Deliberately not square, so height and width can't be mixed up
    return Board(height=2, width=3)


# ---------------------------------------------------------------- structure


def test_contains_every_coord(board: Board):
    for y in range(2):
        for x in range(3):
            assert Coord(x, y) in board

    assert len(board.coords()) == 6


@pytest.mark.parametrize("coord", [Coord(3, 0), Coord(0, 2), Coord(-1, 0)])
def test_does_not_contain_outside_coords(board: Board, coord: Coord):
    assert coord not in board


def test_coords_and_cells_match(board: Board):
    assert {cell.coord for cell in board.cells()} == set(board.coords())


def test_every_cell_starts_in_play(board: Board):
    assert board.in_play        == set(board.coords())


def test_neighbours_are_linked_both_ways(board: Board):
    for cell in board.cells():
        for direction, neighbour in cell.connections.items():
            assert neighbour.coord == cell.coord.to_neighbor(direction)
            assert neighbour.connections[direction.opposite] is cell


def test_every_in_bounds_neighbour_is_linked(board: Board):
    for cell in board.cells():
        for direction in Direction:
            linked = cell.connects(direction)
            exists = cell.coord.to_neighbor(direction) in board

            assert linked == exists, f"{cell.coord} {direction.name}"


@pytest.mark.parametrize("coord, count", [
    (Coord(0, 0), 2),   # corner
    (Coord(1, 0), 3),   # edge
    (Coord(1, 1), 4),   # interior
])
def test_connection_counts(coord: Coord, count: int):
    assert len(Board(3, 3)[coord].connections) == count


# ---------------------------------------------------------------- lookup


def test_getitem(board: Board):
    assert board[Coord(2, 1)].coord == Coord(2, 1)

    with pytest.raises(KeyError):
        board[Coord(5, 5)]


def test_getitem_accepts_tuple(board: Board):
    assert board[(2, 1)] is board[Coord(2, 1)]


def test_contains_accepts_tuple(board: Board):
    assert (2, 1)     in board
    assert (5, 5) not in board


def test_setitem_converts_tuple_key(board: Board):
    cell = Cell((7, 7))
    board[(7, 7)] = cell

    assert board[Coord(7, 7)] is cell
    assert all(type(c) is Coord for c in board.coords())


def test_neighbor(board: Board):
    assert board.neighbor(board[(0, 0)], Direction.EAST) is board[(1, 0)]


def test_neighbor_off_board_raises(board: Board):
    with pytest.raises(CellOutOfBounds):
        board.neighbor(board[(0, 0)], Direction.SOUTH)


def test_expect_returns_existing_cell(board: Board):
    cell = board[Coord(0, 0)]

    assert board.expect(Coord(0, 0)) is cell


def test_expect_creates_missing_cell(board: Board):
    cell = board.expect(Coord(10, 10))

    assert cell.coord == Coord(10, 10)
    assert Coord(10, 10) in board


def test_expect_with_tuple_stores_coord_key(board: Board):
    board.expect((10, 10))

    assert all(type(c) is Coord for c in board.coords())


# ---------------------------------------------------------------- walls


def test_place_wall_disconnects_both_sides(board: Board):
    board.place_wall((0, 0), Direction.EAST)

    assert not board[(0, 0)].connects(Direction.EAST)
    assert not board[(1, 0)].connects(Direction.WEST)


def test_place_wall_leaves_other_connections(board: Board):
    board.place_wall((0, 0), Direction.EAST)

    assert board[(0, 0)].connects(Direction.NORTH)
    assert board[(1, 0)].connects(Direction.EAST)
    assert board[(1, 0)].connects(Direction.NORTH)


# ---------------------------------------------------------------- __str__


def test_str_uses_render_board(board: Board):
    board.place_wall((1, 0), Direction.NORTH)

    assert str(board) == render_board(board)
