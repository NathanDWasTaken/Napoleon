from typing             import Iterable
from abc                import abstractmethod, ABC


from nagrica.grid.direction    import Direction
from nagrica.grid.coord        import Coord, CoordLike








class Board(ABC):
    height:     int
    width:      int

    
    def __init__(self, height: int, width: int) -> None:
        self.height     = height
        self.width      = width

        self.build_board(height, width)


    @abstractmethod
    def build_board(self, height: int, width: int): ...


    # Do and Undo actions

    @abstractmethod
    def place_wall(self, coord: CoordLike, direction: Direction): ...

    @abstractmethod
    def remove_wall(self, coord: CoordLike, direction: Direction): ...

    @abstractmethod
    def capture(self, player_seat: int, coords: Iterable[Coord]): ...

    @abstractmethod
    def release(self, coords: Iterable[Coord]): ...


    # Helper functions

    @abstractmethod
    def owner(self, coord: CoordLike) -> int: ...

    @abstractmethod
    def connects(self, coord: CoordLike, direction: Direction) -> bool: ...

    @abstractmethod
    def is_in_play(self, coord: CoordLike) -> bool: ...

    @property
    @abstractmethod
    def in_play(self) -> Iterable[Coord]: ...



    # Concrete

    @property
    def num_in_play(self) -> int:
        return len(list(self.in_play))

    def coord_is_valid(self, coord: CoordLike) -> bool:
        return (
            0 <= coord[0] < self.width
                    and
            0 <= coord[1] < self.height
        )

