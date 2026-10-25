from typing         import Iterable

from .direction    import Direction
from .cell         import Cell
from .coord        import Coord, CoordLike
from .render       import render_board
from .exceptions   import CellOutOfBounds


class Board:
    height:     int
    width:      int

    _cells:         dict[Coord, Cell]
    in_play:        set[Coord]

    
    def __init__(self, height: int, width: int) -> None:
        self.height     = height
        self.width      = width

        self.build_board(height, width)

    def build_board(self, height: int, width: int):
        self._cells         = {}
        self.in_play        = set()

        for y in range(height):
            for x in range(width):
                coord   = Coord(x, y)
                cell    = self.expect(coord)
                self.in_play.add(coord)

                if 0 < y:
                    self._link_cell(cell, Direction.SOUTH)

                if 0 < x:
                    self._link_cell(cell, Direction.WEST)


    def neighbor(self, cell: Cell, direction: Direction) -> Cell:
        new_coord = cell.coord.to_neighbor(direction)

        if not self.coord_is_valid(new_coord):
            raise CellOutOfBounds()

        return self[new_coord]

    def expect(self, coord: CoordLike) -> Cell:
        if coord not in self:
            self._create_cell(coord)
              
        return self[coord]


    # Actions

    def _link_cell(self, cell: Cell, direction: Direction):

        cell2 = self.neighbor(cell, direction)

        cell .connections[direction]            = cell2
        cell2.connections[direction.opposite]   = cell

    def _create_cell(self, coord: CoordLike):
        self[coord] = Cell(coord)
    

    def place_wall(self, coord: CoordLike, direction: Direction):
        cell    = self[coord]
        cell2   = self.neighbor(cell, direction)
         
        cell .connections.pop(direction, None)
        cell2.connections.pop(direction.opposite, None)


    def register_capture(self, player_i: int, coords: Iterable[CoordLike]):
        for coord in coords:
            self[coord].owned = player_i


    def remove_wall(self, coord: CoordLike, direction: Direction):
        ...


    # Helpers
    
    def coords(self):
        return self._cells.keys()

    def cells(self):
        return self._cells.values()


    # Verification

    def coord_is_valid(self, coord: CoordLike) -> bool:
        return (
            0 <= coord[0] < self.width
                    and
            0 <= coord[1] < self.height
        )

    def neighbor_is_reachable(self, coord: CoordLike, direction: Direction) -> bool:
        return self[coord].connects(direction)


    # Magic
    def __str__(self) -> str:
        return render_board(self)


    def __getitem__(self, coord: CoordLike) -> Cell:
        return self._cells[Coord(*coord)]

    def __setitem__(self, coord: CoordLike, cell: Cell):
        self._cells[Coord(*coord)] = cell

    def __contains__(self, coord: CoordLike) -> bool:
        return coord in self._cells


if __name__ == "__main__":
    b = Board(3, 3)

    print(b)

    b[Coord(0, 0)].owned = 1
    b[Coord(2, 2)].owned = 9

    b.place_wall((1, 1), Direction.NORTH)

    print(b)