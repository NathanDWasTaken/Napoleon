from typing             import Iterable, Self
from abc                import abstractmethod, ABC


from nagrica.grid.coord     import Coord, CoordLike
from nagrica.grid.edge      import Edge
from nagrica.grid.direction import Direction




class Board(ABC):
    height:     int
    width:      int
    in_play:    set[Coord]
    
    _coords:    list[list[Coord]]
    
    def __init__(self, height: int, width: int) -> None:
        self.height     = height
        self.width      = width

        self._coords    = [[Coord(x, y) for x in range(width)] for y in range(height)]
        self.in_play    = set((c for row in self._coords for c in row))
        
        self.build_board(height, width)


    @abstractmethod
    def build_board(self, height: int, width: int): ...


    # Do and Undo actions

    @abstractmethod
    def place_wall(self, wall: Edge): ...

    @abstractmethod
    def remove_wall(self, wall: Edge): ...


    # Helper functions

    @abstractmethod
    def connects(self, edge: Edge) -> bool: ...


    @abstractmethod
    def separated_region(self, start: Coord, end: Coord) -> frozenset[Coord]: ...


    # Concrete

    def capture(self, coords: Iterable[Coord]):
        self.in_play   -= set(coords)

    def release(self, coords: Iterable[Coord]):
        self.in_play  |= set(coords)



    def copy(self: Self) -> Self:
        new: Self = self.__new__(self.__class__)

        new.height      = self.height
        new.width       = self.width

        new.in_play     = self.in_play.copy()
        new._coords     = self._coords

        return new



    @property
    def num_in_play(self) -> int:
        return len(self.in_play)
    
    def is_in_play(self, coord: Coord | tuple[int, int]) -> bool:
        return coord in self.in_play
    
    def coord_is_valid(self, coord: Coord) -> bool:
        return (
            0 <= coord[0] < self.width
                    and
            0 <= coord[1] < self.height
        )


    def edge_is_valid(self, edge: Edge):
        min_width   = 0
        max_width   = self.width
        min_height  = 0
        max_height  = self.height

        match edge.direction:
            case Direction.NORTH:
                max_height -= 1
            case Direction.SOUTH:
                min_height += 1

            case Direction.EAST:
                max_width -= 1
            case Direction.WEST:
                min_width += 1

        return (
            min_width  <= edge.coord[0] < max_width
                    and
            min_height <= edge.coord[1] < max_height
        )

    def __repr__(self):
        return f"{self.__class__.__name__}(width={self.width}, height={self.height})"

