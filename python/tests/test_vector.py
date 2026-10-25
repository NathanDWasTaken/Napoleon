import pytest

from nagrica.grid.vector         import Vector


def test_fields_and_unpacking():
    v = Vector(3, -4)

    assert (v.dx, v.dy) == (3, -4)
    assert tuple(v)     == (3, -4)


def test_length():
    assert Vector(3, 4).length == 5.0
    assert Vector(0, 0).length == 0.0


def test_opposite():
    assert Vector(3, -4).opposite == Vector(-3, 4)


def test_dot():
    assert Vector(1, 2).dot(Vector(3, 4)) == 11
    assert Vector(1, 0).dot(Vector(0, 1)) == 0


@pytest.mark.parametrize("a, b, expected", [
    (Vector(1, 0), Vector( 5,  0),  1.0),     # same direction, length doesn't matter
    (Vector(1, 0), Vector( 0,  2),  0.0),     # perpendicular
    (Vector(1, 0), Vector(-3,  0), -1.0),     # opposite
])
def test_similarity(a: Vector[int], b: Vector[int], expected: float):
    assert a.similarity(b) == pytest.approx(expected)


def test_similarity_with_zero_vector_raises():
    with pytest.raises(ZeroDivisionError):
        Vector(1, 0).similarity(Vector(0, 0))


def test_truediv():
    assert Vector(3, 4) / 2 == Vector(1.5, 2.0)


def test_abs_is_componentwise():
    assert abs(Vector(-3,  4)) == Vector(3, 4)
    assert abs(Vector(-1.5, -2.0)) == Vector(1.5, 2.0)
