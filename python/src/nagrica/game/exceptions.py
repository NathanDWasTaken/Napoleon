from nagrica.exceptions     import NagricaError
from nagrica.grid.edge      import Edge


class IllegalMove(NagricaError):
    def __init__(self, edge: Edge, player_seat: int) -> None:
        super().__init__(f"IllegalMove: Move {edge} by player {player_seat} is not allowed!")