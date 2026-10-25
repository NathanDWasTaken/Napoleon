from random         import Random

from nagrica.game   import Player, Move, GameState



class RandomPlayer(Player):

    def __init__(self, name: str, seat: int, seed: int | None = None) -> None:
        self.random = Random(seed)

        super().__init__(name, seat)

    def make_move(self, gameState: GameState) -> Move:
        all_moves = gameState.legal_moves()

        return self.random.choice(all_moves)