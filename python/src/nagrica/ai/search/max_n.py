from typing             import cast

from nagrica.ai.eval.eval import EvaluationAlgorithm
from nagrica.game       import GameState, Move

from .search            import SearchAlgorithm



class Max_N(SearchAlgorithm):
    max_depth: int


    def __init__(self, eval_algo: EvaluationAlgorithm, *, max_depth: int = 3) -> None:
        self.max_depth  = max_depth

        super().__init__(eval_algo)



    def _recurse_eval(
        self,
        gameState:  GameState,
        *,
        depth:      int = 0
    ) -> list[float]:
        """
        Simple Implementation without pruning
        """

        if gameState.finished:
            return cast(list[float], gameState.scores)


        if depth == self.max_depth:
            return self.eval_algo.evaluate(gameState)

        current_seat    = gameState.current_seat

        best_values: list[float]    = [float("-inf")] * gameState.num_players

        for move in gameState.legal_moves():

            gameState.apply(move)

            values = self._recurse_eval(gameState, depth=depth + 1)

            gameState.undo()

            if values[current_seat] > best_values[current_seat]:
                best_values = values


        return best_values



        



    def select_move(self, gameState: GameState) -> Move:
        best_move           = None
        best_value: float   = float("-inf")
        seat: int           = gameState.current_seat
        
        for move in gameState.legal_moves():
            gameState.apply(move)

            value = self._recurse_eval(gameState)[seat]

            gameState.undo()

            if value > best_value:
                best_value  = value
                best_move   = move

        return cast(Move, best_move)