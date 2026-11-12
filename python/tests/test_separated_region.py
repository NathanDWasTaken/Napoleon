import pytest

from nagrica.game                    import Capture
from nagrica.grid.boards             import LinkedBoard
from nagrica.grid.coord              import Coord
from nagrica.grid.direction          import Direction
from nagrica.grid.vector             import Vector


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
