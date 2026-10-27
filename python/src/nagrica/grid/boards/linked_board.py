from typing     import Iterable

from .board     import Board

from nagrica.grid.direction     import Direction
from nagrica.grid.cell          import Cell
from nagrica.grid.coord         import Coord, CoordLike
from nagrica.grid.exceptions    import CellOutOfBounds


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

