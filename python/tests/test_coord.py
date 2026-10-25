import pytest

from nagrica.grid   import Direction, Vector, Coord


def test_equality_and_hash():
    assert Coord(1, 2) == Coord(1, 2)
    assert Coord(1, 2) != Coord(2, 1)
    assert len({Coord(1, 2), Coord(1, 2)}) == 1


def test_equals_plain_tuple():
    assert Coord(1, 2) == (1, 2)
    assert hash(Coord(1, 2)) == hash((1, 2))


def test_unpacks():
    x, y = Coord(1, 2)

    assert (x, y) == (1, 2)


def test_is_frozen():
    coord = Coord(1, 2)

    with pytest.raises(AttributeError):
        coord.x = 5     # pyright: ignore[reportAttributeAccessIssue]


# ---------------------------------------------------------------- to_neighbor


@pytest.mark.parametrize("direction, expected", [
    (Direction.NORTH, Coord(1, 2)),
    (Direction.EAST,  Coord(2, 1)),
    (Direction.SOUTH, Coord(1, 0)),
    (Direction.WEST,  Coord(0, 1)),
])
def test_to_neighbor(direction: Direction, expected: Coord):
    assert Coord(1, 1).to_neighbor(direction) == expected


def test_to_neighbor_returns_coord():
    assert type(Coord(1, 1).to_neighbor(Direction.NORTH)) is Coord


@pytest.mark.parametrize("direction", Direction)
def test_to_neighbor_there_and_back(direction: Direction):
    origin = Coord(3, 4)

    assert origin.to_neighbor(direction).to_neighbor(direction.opposite) == origin


# ---------------------------------------------------------------- direction_to


@pytest.mark.parametrize("direction", Direction)
def test_direction_to_neighbour(direction: Direction):
    origin = Coord(1, 1)

    assert origin.direction_to(origin.to_neighbor(direction)) is direction


def test_direction_to_accepts_tuple():
    assert Coord(1, 1).direction_to((1, 2)) is Direction.NORTH


@pytest.mark.parametrize("other", [(3, 1), (2, 2), (1, 1)])
def test_direction_to_non_neighbour_raises(other: tuple[int, int]):
    with pytest.raises(ValueError):
        Coord(1, 1).direction_to(other)


# ---------------------------------------------------------------- offset_to


@pytest.mark.parametrize("other, expected", [
    (Coord(4, -1),  Vector( 3, -2)),
    ((1, 1),        Vector( 0,  0)),
    ((0, 5),        Vector(-1,  4)),
])
def test_offset_to(other: Coord | tuple[int, int], expected: Vector[int]):
    offset = Coord(1, 1).offset_to(other)

    assert offset == expected
    assert isinstance(offset, Vector)
