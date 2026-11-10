from random                     import Random

import pytest

from nagrica.ai.eval             import CurrentScore
from nagrica.ai.search.max_n     import Max_N
from nagrica.game                import BasicGameState
from nagrica.grid.boards         import Board


def random_positions(board_class: type[Board], num_players: int, seed: int, count: int = 12):
    rng     = Random(seed)
    state   = BasicGameState(3, 3, num_players, board_class=board_class)

    for _ in range(count):
        if state.finished:
            return
        yield state
        state.apply(rng.choice(state.legal_moves()))


@pytest.mark.parametrize("num_players", [2, 3])
@pytest.mark.parametrize("depth",       [1, 2, 3, 4])
@pytest.mark.parametrize("seed",        range(5))
def test_pruned_matches_unpruned(board_class: type[Board], num_players: int, depth: int, seed: int):
    search = Max_N(CurrentScore(), max_depth=depth)

    for state in random_positions(board_class, num_players, seed):
        _, plain  = search._dfs_eval       (state, max_depth=depth)
        _, pruned = search._dfs_eval_pruned(state, max_depth=depth)

        assert pruned == plain, f"history={state.history}"
