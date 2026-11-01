import asyncio
from typing             import cast, Callable
from logging            import getLogger

from nagrica.ai.eval    import EvaluationAlgorithm
from nagrica.game       import BasicGameState
from nagrica.grid       import Edge

from .search            import SearchAlgorithm

from nagrica.ui         import render_board


logger = getLogger(__name__)


render_state: Callable[[BasicGameState], str] = lambda state: render_board(state.board)


class Max_N(SearchAlgorithm):
    max_depth:  int | float
    max_time:   int | float


    _signal_end:    asyncio.Event


    def __init__(self, eval_algo: EvaluationAlgorithm, *, max_depth: int | None = 3, max_time: int | None = None) -> None:
        self.max_depth  = max_depth if max_depth is not None else float("+inf")
        self.max_time   = max_time  if max_time  is not None else float("+inf")

        self._signal_end    = asyncio.Event()

        super().__init__(eval_algo)






    async def _wait_compute_time(self):
        if self.max_time == float("+inf"):
            logger.info("Max time disabled, running full DFS.")
            return
        
        logger.info(f"Giving the comp {self.max_time}s")
        
        await asyncio.sleep(self.max_time)

        logger.info(f"Ran for {self.max_time}s")

        self._signal_end.set()




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


    def _dfs_eval(
        self,
        gameState:  BasicGameState,
        max_depth:  int,
        *,
        depth:      int                 = 0,
        move_order: list[Edge] | None   = None,
    ) -> tuple[Edge | None, list[float]]:
        """
        Simple Implementation without pruning
        """

        if gameState.finished or depth == max_depth:
            return None, self.eval_algo.evaluate(gameState)

        current_seat    = gameState.current_seat

        best_move                   = None
        best_values: list[float]    = [float("-inf")] * gameState.num_players

        if move_order is None:
            all_moves = gameState.legal_moves()
        else:    
            all_moves = move_order


        for move in all_moves:

            if self._signal_end.is_set():
                return best_move, best_values

            gameState.apply(move)

            _, values = self._dfs_eval(gameState, max_depth=max_depth, depth=depth + 1)

            gameState.undo()

            if self._move_value_is_better(current_seat, best_values, values):
                best_values = values
                best_move   = move


        return best_move, best_values


    def _iterative_dfs_eval(
        self,
        gameState:  BasicGameState,
    ) -> tuple[Edge, list[float]]:

        best_values = None
        best_move   = None

        depth = 1

        while not self._signal_end.is_set() and depth <= self.max_depth:
            move_order = None
            if best_move is not None:
                move_order = [best_move] + [m for m in gameState.legal_moves() if m != best_move]

            (best_move, best_values) = self._dfs_eval(gameState, max_depth=depth, move_order=move_order)
            depth += 1


        return (cast(Edge, best_move), cast(list[float], best_values))





    async def async_select_move(self, gameState:  BasicGameState) -> Edge:
        
        self._signal_end.clear()

        # If search cancel takes too long, consider implementing forceful stop
        # async with asyncio.timeout(self.max_time):

        
        _, (move, _) = await asyncio.gather(
            self._wait_compute_time(),
            asyncio.to_thread(self._iterative_dfs_eval, gameState)
        )

        return move
        


    def select_move(self, gameState: BasicGameState) -> Edge:
        return asyncio.run(self.async_select_move(gameState))