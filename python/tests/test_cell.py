import pytest

from nagrica.grid.cell           import Cell
from nagrica.grid.exceptions     import CellOutOfBounds
from nagrica.grid.coord          import Coord
from nagrica.grid.direction      import Direction


def test_new_cell():
    cell = Cell(Coord(2, 3))

    assert cell.coord       == Coord(2, 3)
    assert cell.owned       == -1
    assert cell.connections == {}


def test_tuple_coord_is_converted():
    cell = Cell((2, 3))

    assert type(cell.coord) is Coord
    assert cell.coord       == Coord(2, 3)


def test_xy_properties():
    cell = Cell(Coord(2, 3))

    assert cell.x == 2
    assert cell.y == 3


def test_connections_are_not_shared():
    a = Cell(Coord(0, 0))
    b = Cell(Coord(1, 0))

    assert a.connections is not b.connections


def test_connects():
    a = Cell(Coord(0, 0))
    b = Cell(Coord(1, 0))
    a.connections[Direction.EAST] = b

    assert     a.connects(Direction.EAST)
    assert not a.connects(Direction.WEST)


def test_walk_follows_connection():
    a = Cell(Coord(0, 0))
    b = Cell(Coord(1, 0))
    a.connections[Direction.EAST] = b

    assert a.walk(Direction.EAST) is b


def test_walk_without_connection_raises():
    with pytest.raises(CellOutOfBounds):
        Cell(Coord(0, 0)).walk(Direction.NORTH)
