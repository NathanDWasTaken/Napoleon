from abc            import ABC, abstractmethod

from .state         import CompleteGameState
from nagrica.grid   import Edge


class Player(ABC):
    name:   str
    seat:   int # Position/id of the player. Starts at 0 and increases


    def __init__(self, name: str, seat: int) -> None:
        self.name   = name
        self.seat   = seat


    @abstractmethod
    def make_move(self, gameState: CompleteGameState) -> Edge:
        ...