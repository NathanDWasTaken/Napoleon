from typing     import Iterable

from .board     import Board

from nagrica.grid.direction     import Direction
from nagrica.grid.coord         import Coord, CoordLike
from nagrica.grid.exceptions    import CellOutOfBounds



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
        



class LinkedBoard(Board):

    _in_play:       set[Coord]
    _cells:         dict[Coord, Cell]

    def build_board(self, height: int, width: int):
        self._in_play   = set()
        self._cells     = {}

        for y in range(height):
            for x in range(width):
                coord   = Coord(x, y)
                self._create_cell(coord)
                self._in_play.add(coord)

                if 0 < y:
                    self._link_cell(coord, Direction.SOUTH)

                if 0 < x:
                    self._link_cell(coord, Direction.WEST)


    def place_wall(self, coord: CoordLike, direction: Direction):
        cell    = self[coord]
        other   = cell.walk(direction)
         
        cell .connections.pop(direction, None)
        other.connections.pop(direction.opposite, None)


    def remove_wall(self, coord: CoordLike, direction: Direction):
        if not self.coord_is_valid(Coord(*coord).to_neighbor(direction)):
            raise CellOutOfBounds()

        self._link_cell(coord, direction)


    def capture(self, player_seat: int, coords: Iterable[Coord]):
        coords          = set(coords)
        self._in_play  -= coords
        for coord in coords:
            self[coord].owned = player_seat

    def release(self, coords: Iterable[Coord]):
        coords          = set(coords)
        self._in_play  |= coords
        for coord in coords:
            self[coord].owned = -1


    def owner(self, coord: CoordLike) -> int:
        return self[coord].owned

    def connects(self, coord: CoordLike, direction: Direction) -> bool:
        return self[coord].connects(direction)
    

    def is_in_play(self, coord: Coord | tuple[int, int]) -> bool:
        return coord in self._in_play

    @property
    def in_play(self) -> Iterable[Coord]:
        return self._in_play


    def copy(self):
        new             = LinkedBoard.__new__(LinkedBoard)
        
        new.height      = self.height
        new.width       = self.width

        new._in_play    = self._in_play.copy()

        new._cells      = {}


        for y in range(self.height):
            for x in range(self.width):
                coord   = Coord(x, y)
                new._create_cell(coord)

                old_cell    = self[coord]
                new_cell    = new[coord]

                new_cell.owned = old_cell.owned

                for dir in [Direction.SOUTH, Direction.WEST]:
                    if old_cell.connects(dir):
                        new._link_cell(coord, dir)

        return new




    # Specific to this class

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

