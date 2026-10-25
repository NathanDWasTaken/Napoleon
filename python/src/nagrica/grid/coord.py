from typing         import NamedTuple

from .direction    import Direction
from .vector       import Vector


class Coord(NamedTuple):
    x: int
    y: int


    def to_neighbor(self, direction: Direction) -> Coord:
        return Coord(
            self.x + direction.dx, 
            self.y + direction.dy
        )


    def direction_to(self, other: CoordLike) -> Direction:
        ox, oy = other
        return Direction(
            ox - self.x,
            oy - self.y
        )


    def offset_to(self, other: CoordLike) -> Vector[int]:
        ox, oy = other
        return Vector(
            ox - self.x,
            oy - self.y
        )



CoordLike = Coord | tuple[int, int]


if __name__ == "__main__":
    ...

