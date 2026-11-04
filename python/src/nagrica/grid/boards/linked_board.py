from typing     import Self

from .board     import Board

from nagrica.grid.vector        import Vector
from nagrica.grid.direction     import Direction
from nagrica.grid.coord         import Coord, CoordLike
from nagrica.grid.exceptions    import CoordOutOfBounds
from nagrica.grid.edge          import Edge


class Cell:
    coord:          Coord

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
            raise CoordOutOfBounds()

        return self.connections[direction]


    def __repr__(self) -> str:
        connections_str = ", ".join(f"{d.name[0]}=({c.coord.x},{c.coord.y})" for d, c in self.connections.items())

        return f"Cell(coord={self.coord}, connections=({connections_str}))"
        



class LinkedBoard(Board):
    _cells:         dict[Coord, Cell]

    def build_board(self, height: int, width: int):
        self._cells     = {}

        for y in range(height):
            for x in range(width):
                coord   = Coord(x, y)
                self._create_cell(coord)

                if 0 < y:
                    self._link_cell(coord, Direction.SOUTH)

                if 0 < x:
                    self._link_cell(coord, Direction.WEST)


    def place_wall(self, wall: Edge):
        self.ensure_valid_edge(wall)

        cell    = self[wall.coord]
        other   = cell.walk(wall.direction)
         
        cell .connections.pop(wall.direction, None)
        other.connections.pop(wall.direction.opposite, None)


    def remove_wall(self, wall: Edge):
        self.ensure_valid_edge(wall)

        self._link_cell(wall.coord, wall.direction)


    def connects(self, edge: Edge) -> bool:
        if not self.edge_is_valid(edge):
            return False
        return self[edge.coord].connects(edge.direction)


    def copy(self) -> Self:
        new = super().copy()

        new._cells  = {}

        for y in range(self.height):
            for x in range(self.width):
                coord   = Coord(x, y)
                new._create_cell(coord)


                for dir in [Direction.SOUTH, Direction.WEST]:
                    if self[coord].connects(dir):
                        new._link_cell(coord, dir)

        return new


    # Specific to this class

    @staticmethod
    def _direction_order(offset: Vector[int]) -> tuple[Direction, ...]:
        return tuple(sorted(
            Direction,
            key     = lambda d: offset.similarity(d),
            reverse = True
        ))




    def _traverse(
        self,
        point:          Coord
    ):
        self.visited.add(point)
        
        if point == self._goal:
            return True
        
        offset      = point.offset_to(self._goal)
        directions  = self._direction_order(offset)

        for direction in directions:
            if not self.connects(Edge(point, direction)):
                continue

            neighbor = point.to_neighbor(direction)

            if neighbor in self.visited:
                continue

            result = self._traverse(neighbor)

            if result:
                return True

        return False


    def separated_region(self, start: CoordLike, end: CoordLike) -> frozenset[Coord]:
        start, end                  = Coord(*start), Coord(*end)
        self.visited: set[Coord]    = set()
        self._goal                  = end

        result = self._traverse(start)

        if result:
            return frozenset()

        return frozenset(self.visited)



    def _create_cell(self, coord: CoordLike):
        coord               = Coord(*coord)
        self._cells[coord]  = Cell(coord)

    
    def _link_cell(self, coord: CoordLike, direction: Direction):
        coord       = Coord(*coord)
        cell        = self[coord]
        other_coord = coord.to_neighbor(direction)
        other_cell  = self[other_coord]

        cell      .connections[direction]            = other_cell
        other_cell.connections[direction.opposite]   = cell


    def __getitem__(self, coord: CoordLike) -> Cell:
        return self._cells[Coord(*coord)]

    def __contains__(self, coord: CoordLike) -> bool:
        return coord in self._cells

