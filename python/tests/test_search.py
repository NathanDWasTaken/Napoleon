from nagrica.ai                  import RandomMove
from nagrica.capture             import GreedyDFS
from nagrica.game                import GameState
from nagrica.grid.boards         import Board


def new_state(board_class: type[Board], height: int = 3, width: int = 3) -> GameState:
    return GameState(height, width, 2, capture_eval=GreedyDFS, board_class=board_class)


# ---------------------------------------------------------------- RandomMove


def test_random_move_only_picks_legal_moves(board_class: type[Board]):
    state   = new_state(board_class, 4, 4)
    search  = RandomMove(seed=1)

    while not state.finished:
        move = search.select_move(state)

        assert state.is_legal(move)
        state.apply(move)


def test_random_move_is_reproducible_with_seed(board_class: type[Board]):
    state   = new_state(board_class, 5, 5)
    first   = RandomMove(seed=42)
    second  = RandomMove(seed=42)

    assert (
        [first .select_move(state) for _ in range(10)] ==
        [second.select_move(state) for _ in range(10)]
    )


def test_random_move_without_seed(board_class: type[Board]):
    state = new_state(board_class)

    assert state.is_legal(RandomMove().select_move(state))
