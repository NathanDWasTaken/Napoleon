from dataclasses    import dataclass


from nagrica.grid.coord     import Coord
from nagrica.grid.direction import Direction


@dataclass(frozen=True)
class Edge:
    coord:      Coord
    direction:  Direction

    def __hash__(self) -> int:
        return hash(frozenset((self.coord, self.other)))

    @property
    def other(self):
        return self.coord.to_neighbor(self.direction)