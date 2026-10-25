from .direction         import Direction
from .coord             import Coord, CoordLike
from .exceptions        import CellOutOfBounds



class Cell:
    coord:          Coord
    owned:          int = -1

    connections:    dict[Direction, Cell]

    def __init__(self, coord: CoordLike) -> None:
        self.coord          = Coord(*coord)
        self.connections    = {}
    
    
    @property
    def x(self) -> int:
        return self.coord.x

    @property
    def y(self) -> int:
        return self.coord.y


    def connects(self, direction: Direction) -> bool:
        return direction in self.connections

    def walk(self, direction: Direction) -> Cell:
        if not self.connects(direction):
            raise CellOutOfBounds()

        return self.connections[direction]


    def __repr__(self) -> str:
        connections_str = ", ".join(f"{d.name[0]}=({c.coord.x},{c.coord.y})" for d, c in self.connections.items())

        return f"Cell(coord={self.coord}, owned={self.owned}, connections=({connections_str}))"