from typing             import cast, Callable

from nagrica.ai.eval    import EvaluationAlgorithm
from nagrica.game       import GameState, Move

from .search            import SearchAlgorithm

from nagrica.ui         import render_board


render_state: Callable[[GameState], str] = lambda state: render_board(state.board)


class Max_N(SearchAlgorithm):
    max_depth: int


    def __init__(self, eval_algo: EvaluationAlgorithm, *, max_depth: int = 3) -> None:
        self.max_depth  = max_depth

        super().__init__(eval_algo)



    def _recurse_eval(
        self,
        gameState:  GameState,
        *,
        depth:      int = 1
    ) -> list[float]:
        """
        Simple Implementation without pruning
        """

        if gameState.finished or depth == self.max_depth:
            return self.eval_algo.evaluate(gameState)

        current_seat    = gameState.current_seat

        best_values: list[float]    = [float("-inf")] * gameState.num_players

        for move in gameState.legal_moves():

            gameState.apply(move)

            values = self._recurse_eval(gameState, depth=depth + 1)

            gameState.undo()

            if self._move_value_is_better(current_seat, best_values, values):
                best_values = values


        return best_values


    @staticmethod
    def _move_value_is_better(seat: int, best_values: list[float], values: list[float]) -> bool:
        val         = values[seat]
        best_val    = best_values[seat]

        # Value for player is better than best so far
        # or
        # Value for player is equal  and the other players have less
        return (
            (val > best_val)
                or
            (val == best_val and sum(values) < sum(best_values))
        )



    def select_move(self, gameState: GameState) -> Move:
        best_move                   = None
        best_values: list[float]    = [float("-inf")] * gameState.num_players
        seat: int                   = gameState.current_seat
        
        for move in gameState.legal_moves():
            gameState.apply(move)

            values  = self._recurse_eval(gameState)

            gameState.undo()

            if self._move_value_is_better(seat, best_values, values):
                best_values = values
                best_move   = move

        
        return cast(Move, best_move)