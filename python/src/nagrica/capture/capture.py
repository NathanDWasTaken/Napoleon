from functools      import lru_cache
from dataclasses    import dataclass
from abc            import ABC, abstractmethod


from nagrica.grid   import Board, Direction, Vector, Coord, CoordLike


@dataclass(frozen=True)
class Capture:
    coords: frozenset[Coord]

    @property
    def points(self):
        return len(self.coords)

    @property
    def split(self):
        # Checks whether there is a new split (A new capture has taken place)
        return self.points > 0



class CaptureEvaluation(ABC):
    board: Board


    def __init__(self, board: Board) -> None:
        self.board = board


    @abstractmethod
    def run(self, start: CoordLike, end: CoordLike) -> Capture:         
        ...


    @staticmethod
    @lru_cache
    def _direction_order(offset: Vector[int]) -> tuple[Direction, ...]:
        return tuple(sorted(
            Direction,
            key     = lambda d: offset.similarity(d),
            reverse = True
        ))

