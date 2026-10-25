from nagrica.exceptions     import NagricaError
from nagrica.game.move      import Move


class IllegalMove(NagricaError):
    def __init__(self, move: Move, player_seat: int) -> None:
        super().__init__(f"IllegalMove: Move {move} by player {player_seat} is not allowed!")