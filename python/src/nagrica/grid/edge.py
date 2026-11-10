from functools      import lru_cache

from dataclasses    import dataclass


from nagrica.grid.coord     import Coord
from nagrica.grid.direction import Direction

@lru_cache
def edge_hash(x: int, y: int, direction: Direction) -> int:
    match direction:
        case Direction.NORTH | Direction.EAST:
            return hash(((x, y), direction))
            
        case Direction.WEST:
            return hash(((x - 1, y), Direction.EAST))
        
        case Direction.SOUTH:
            return hash(((x, y - 1), Direction.NORTH))


@dataclass(frozen=True)
class Edge:
    coord:      Coord
    direction:  Direction

    def __hash__(self) -> int:
        return edge_hash(self.coord.x, self.coord.y, self.direction)

    @property
    def other(self):
        return self.coord.to_neighbor(self.direction)