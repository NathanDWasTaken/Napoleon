from typing             import Iterable, Self
from abc                import abstractmethod, ABC


from nagrica.grid.coord     import Coord, CoordLike
from nagrica.grid.edge      import Edge
from nagrica.grid.exceptions    import CoordOutOfBounds




class Board(ABC):
    height:     int
    width:      int
    in_play:    set[Coord]
    
    def __init__(self, height: int, width: int) -> None:
        self.height     = height
        self.width      = width
        self.in_play    = set([Coord(x, y) for x in range(width) for y in range(height)])

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
    def separated_region(self, start: CoordLike, end: CoordLike) -> frozenset[Coord]: ...


    # Concrete

    def capture(self, coords: Iterable[Coord]):
        self.in_play   -= set(coords)

    def release(self, coords: Iterable[Coord]):
        self.in_play  |= set(coords)



    def copy(self: Self) -> Self:
        new: Self = self.__new__(self.__class__)

        new.height  = self.height
        new.width   = self.width

        new.in_play = self.in_play.copy()

        return new



    @property
    def num_in_play(self) -> int:
        return len(self.in_play)
    
    def is_in_play(self, coord: Coord | tuple[int, int]) -> bool:
        return coord in self.in_play
    
    def coord_is_valid(self, coord: CoordLike) -> bool:
        return (
            0 <= coord[0] < self.width
                    and
            0 <= coord[1] < self.height
        )


    def edge_is_valid(self, edge: Edge):
        return (
            self.coord_is_valid(edge.coord)
                    and
            self.coord_is_valid(edge.other)
        )

    def ensure_valid_edge(self, edge: Edge):
        if not self.edge_is_valid(edge):
            raise CoordOutOfBounds()

    def __repr__(self):
        return f"{self.__class__.__name__}(width={self.width}, height={self.height})"

