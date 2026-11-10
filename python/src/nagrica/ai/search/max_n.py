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
        if max_depth is None and max_time is None:
            raise ValueError("Need one of the 2 values set: max_time, max_depth.")

        self.max_depth  = max_depth if max_depth is not None else float("+inf")
        self.max_time   = max_time  if max_time  is not None else float("+inf")

        self._signal_end    = asyncio.Event()

        super().__init__(eval_algo)



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


    def _dfs_eval_pruned(
        self,
        gameState:  BasicGameState,
        max_depth:  int,
        *,
        depth:              int                 = 0,
        move_order:         list[Edge] | None   = None,
        parent_best_values: list[float] | None  = None,
    ) -> tuple[Edge | None, list[float]]:
        """
        Simple Implementation without pruning
        """

        if gameState.finished or depth == max_depth:
            return None, self.eval_algo.evaluate(gameState)

        current_seat    = gameState.current_seat
        prev_seat       = (current_seat - 1) % gameState.num_players

        best_move                   = None
        best_values: list[float]    = [float("-inf")] * gameState.num_players
        
        if parent_best_values is None:
            parent_best_values = [float("-inf")] * gameState.num_players

        if move_order is None:
            all_moves = gameState.legal_moves()
        else:    
            all_moves = move_order



        for move in all_moves:

            if self._signal_end.is_set():
                return best_move, best_values

            gameState.apply(move)

            _, values = self._dfs_eval_pruned(gameState, max_depth=max_depth, depth=depth + 1, parent_best_values=best_values)

            gameState.undo()

            if self._move_value_is_better(current_seat, best_values, values):
                best_values = values
                best_move   = move

            if (gameState.board.height * gameState.board.width) - best_values[current_seat] < parent_best_values[prev_seat]:
                return best_move, best_values


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

            (new_move, new_values) = self._dfs_eval_pruned(gameState, max_depth=depth, move_order=move_order)
            depth += 1

            if not self._signal_end.is_set():
                best_move   = new_move
                best_values = new_values


        return (cast(Edge, best_move), cast(list[float], best_values))



    async def _wait_compute_time(self):
        if self.max_time == float("+inf"):
            logger.info("Max time disabled, running full DFS.")
            return
        
        logger.info(f"Giving the comp {self.max_time}s")
        
        await asyncio.sleep(self.max_time)

        logger.info(f"Ran for {self.max_time}s")

        self._signal_end.set()


    async def _run_dfs(self, gameState: BasicGameState, timer: asyncio.Task):
        try:
            result = await asyncio.to_thread(self._iterative_dfs_eval, gameState)

        finally:
            timer.cancel()

        return result


    async def async_select_move(self, gameState:  BasicGameState) -> Edge:
        
        self._signal_end.clear()

        # If search cancel takes too long, consider implementing forceful stop
        # async with asyncio.timeout(self.max_time):

        timer   = asyncio.create_task(self._wait_compute_time())
        move, _ = await self._run_dfs(gameState, timer)

        return move
        


    def select_move(self, gameState: BasicGameState) -> Edge:
        return asyncio.run(self.async_select_move(gameState))