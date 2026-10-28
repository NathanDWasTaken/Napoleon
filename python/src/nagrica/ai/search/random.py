from random         import Random

from nagrica.game   import GameState, Move
from .search        import SearchAlgorithm



class RandomMove(SearchAlgorithm):
    # Picks uniformly from the legal moves, so it needs no evaluation algorithm
    random: Random

    def __init__(self, *, seed: int | None = None) -> None:
        self.random     = Random(seed)



    def select_move(self, gameState: GameState) -> Move:
        all_moves = gameState.legal_moves()

        return self.random.choice(all_moves)
