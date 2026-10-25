import pytest

from nagrica.grid.direction      import Direction, N, E, S, W
from nagrica.grid.vector         import Vector


@pytest.mark.parametrize("direction, delta", [
    (Direction.NORTH, ( 0,  1)),
    (Direction.EAST,  ( 1,  0)),
    (Direction.SOUTH, ( 0, -1)),
    (Direction.WEST,  (-1,  0)),
])
def test_deltas(direction: Direction, delta: tuple[int, int]):
    assert (direction.dx, direction.dy) == delta


@pytest.mark.parametrize("direction, opposite", [
    (Direction.NORTH, Direction.SOUTH),
    (Direction.EAST,  Direction.WEST),
    (Direction.SOUTH, Direction.NORTH),
    (Direction.WEST,  Direction.EAST),
])
def test_opposite(direction: Direction, opposite: Direction):
    assert direction.opposite is opposite


@pytest.mark.parametrize("direction", Direction)
def test_opposite_twice_is_identity(direction: Direction):
    assert direction.opposite.opposite is direction


def test_lookup_by_delta():
    assert Direction((1, 0))         is Direction.EAST
    assert Direction(Vector(0, -1))  is Direction.SOUTH


def test_short_aliases():
    assert (N, E, S, W) == (Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST)


@pytest.mark.parametrize("direction", Direction)
def test_is_unit_vector(direction: Direction):
    assert isinstance(direction, Vector)
    assert direction.length == 1


def test_usable_as_dict_key():
    assert {Direction.NORTH: 1}[Direction.NORTH] == 1
