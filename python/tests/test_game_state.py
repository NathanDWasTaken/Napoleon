from random         import Random

import pytest

from nagrica.capture             import Capture, GreedyDFS
from nagrica.game                import GameState, IllegalMove, Move
from nagrica.grid.boards         import Board
from nagrica.grid.coord          import Coord
from nagrica.grid.direction      import Direction


N, E, S, W = Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST


def new_state(board_class: type[Board], height: int = 3, width: int = 3, num_players: int = 2) -> GameState:
    return GameState(
        height,
        width,
        num_players,
        capture_eval    = GreedyDFS,
        board_class     = board_class,
    )


@pytest.fixture
def state(board_class: type[Board]) -> GameState:
    return new_state(board_class)


# ---------------------------------------------------------------- initial state


def test_initial_state(state: GameState):
    assert state.scores         == [0, 0]
    assert state.history        == []
    assert state.current_seat   == 0
    assert not state.finished


# ---------------------------------------------------------------- legality


def test_legal_moves_on_fresh_board(board_class: type[Board]):
    # Every internal wall: height * (width - 1) vertical + width * (height - 1) horizontal
    state = new_state(board_class, height=2, width=3)

    assert len(state.legal_moves()) == 2 * 2 + 3 * 1


def test_legal_moves_list_each_wall_once(state: GameState):
    moves = state.legal_moves()

    assert len(set(moves)) == len(moves)
    assert all(move.direction in (N, E) for move in moves)


def test_every_legal_move_is_legal(state: GameState):
    for move in state.legal_moves():
        assert state.is_legal(move)


def test_both_sides_of_a_wall_are_legal(state: GameState):
    assert state.is_legal(Move(Coord(0, 0), N))
    assert state.is_legal(Move(Coord(0, 1), S))


@pytest.mark.parametrize("move", [
    Move(Coord(0, 0), S),   # outer edge
    Move(Coord(2, 2), E),   # outer edge
    Move(Coord(5, 5), N),   # off the board
], ids=["south-edge", "east-edge", "off-board"])
def test_is_legal_rejects_board_edges(state: GameState, move: Move):
    assert not state.is_legal(move)


def test_is_legal_rejects_existing_wall(state: GameState):
    state.apply(Move(Coord(0, 0), E))

    assert not state.is_legal(Move(Coord(0, 0), E))
    assert not state.is_legal(Move(Coord(1, 0), W))


def test_is_legal_rejects_captured_cells(state: GameState):
    # Seal off (0, 0), then try to wall it in further
    state.apply(Move(Coord(0, 0), N))
    state.apply(Move(Coord(0, 0), E))

    assert not state.is_legal(Move(Coord(0, 0), E))
    assert Move(Coord(0, 0), E) not in state.legal_moves()


def test_apply_illegal_move_raises(state: GameState):
    with pytest.raises(IllegalMove):
        state.apply(Move(Coord(0, 0), S))


def test_illegal_move_leaves_state_unchanged(state: GameState):
    with pytest.raises(IllegalMove):
        state.apply(Move(Coord(0, 0), S))

    assert state.history        == []
    assert state.current_seat   == 0


# ---------------------------------------------------------------- turns


def test_apply_advances_seat_and_records_turn(state: GameState):
    move = Move(Coord(0, 0), E)
    state.apply(move)

    assert state.current_seat           == 1
    assert len(state.history)           == 1
    assert state.history[0].player_seat == 0
    assert state.history[0].move        == move
    assert state.history[0].capture     == Capture(frozenset())


def test_seats_wrap_around(board_class: type[Board]):
    state = new_state(board_class, height=4, width=4, num_players=3)

    for seat in (0, 1, 2, 0):
        assert state.current_seat == seat
        state.apply(state.legal_moves()[0])


# ---------------------------------------------------------------- captures


def test_capture_scores_for_the_mover(state: GameState):
    state.apply(Move(Coord(0, 0), N))   # seat 0, no capture
    state.apply(Move(Coord(0, 0), E))   # seat 1, seals off (0, 0)

    assert state.scores                 == [0, 1]
    assert state.board.owner((0, 0))    == 1
    assert not state.board.is_in_play((0, 0))
    assert state.history[-1].capture    == Capture(frozenset({Coord(0, 0)}))


def test_last_two_cells_both_go_to_the_mover(board_class: type[Board]):
    state = new_state(board_class, height=1, width=2)

    state.apply(Move(Coord(0, 0), E))

    assert state.scores     == [2, 0]
    assert state.finished


# ---------------------------------------------------------------- full games


@pytest.mark.parametrize("height, width", [(2, 2), (3, 4), (5, 5)])
@pytest.mark.parametrize("seed", range(5))
def test_random_game_hands_out_every_cell(board_class: type[Board], height: int, width: int, seed: int):
    rng     = Random(seed)
    state   = new_state(board_class, height, width)

    while not state.finished:
        moves = state.legal_moves()

        assert moves, "game is not finished, but there are no legal moves"
        state.apply(rng.choice(moves))

    assert sum(state.scores)        == height * width
    assert state.board.num_in_play  == 0

    for seat, score in enumerate(state.scores):
        owned = [
            coord
            for y in range(height)
            for x in range(width)
            if state.board.owner(coord := Coord(x, y)) == seat
        ]

        assert len(owned) == score


# ---------------------------------------------------------------- copy


def board_snapshot(state: GameState) -> tuple:
    board   = state.board
    coords  = [Coord(x, y) for y in range(board.height) for x in range(board.width)]

    return (
        frozenset((coord, direction) for coord in coords for direction in Direction if board.connects(coord, direction)),
        {coord: board.owner(coord) for coord in coords},
        frozenset(board.in_play),
    )


def snapshot(state: GameState) -> tuple:
    """Everything observable about a game state."""
    return (
        board_snapshot(state),
        tuple(state.scores),
        tuple(state.history),
        state.current_seat,
        state.finished,
    )


def played_state(board_class: type[Board], seed: int, moves: int = 10) -> GameState:
    """A 4x4 game, part way through, with some captures."""
    rng     = Random(seed)
    state   = new_state(board_class, 4, 4)

    for _ in range(moves):
        state.apply(rng.choice(state.legal_moves()))

    return state


def test_copy_has_every_field(state: GameState):
    # Catches a field added to __init__ but forgotten in copy()
    assert vars(state.copy()).keys() == vars(state).keys()


def test_copy_has_every_field_mid_game(board_class: type[Board]):
    state = played_state(board_class, 0)

    assert vars(state.copy()).keys() == vars(state).keys()


def test_copy_of_fresh_state_matches(state: GameState):
    assert snapshot(state.copy()) == snapshot(state)


@pytest.mark.parametrize("seed", range(5))
def test_copy_matches_mid_game(board_class: type[Board], seed: int):
    state = played_state(board_class, seed)

    assert snapshot(state.copy()) == snapshot(state)


def test_copy_keeps_board_class_and_capture_eval(board_class: type[Board]):
    clone = played_state(board_class, 0).copy()

    assert type(clone.board)    is board_class
    assert clone._ce            is GreedyDFS


def test_copy_does_not_share_mutable_parts(state: GameState):
    clone = state.copy()

    assert clone.board      is not state.board
    assert clone.scores     is not state.scores
    assert clone.history    is not state.history


@pytest.mark.parametrize("seed", range(3))
def test_playing_on_copy_leaves_original(board_class: type[Board], seed: int):
    state   = played_state(board_class, seed)
    before  = snapshot(state)
    clone   = state.copy()
    rng     = Random(seed)

    while not clone.finished:
        clone.apply(rng.choice(clone.legal_moves()))

    assert snapshot(state) == before


@pytest.mark.parametrize("seed", range(3))
def test_playing_on_original_leaves_copy(board_class: type[Board], seed: int):
    state   = played_state(board_class, seed)
    clone   = state.copy()
    before  = snapshot(clone)
    rng     = Random(seed)

    while not state.finished:
        state.apply(rng.choice(state.legal_moves()))

    assert snapshot(clone) == before


@pytest.mark.parametrize("seed", range(3))
def test_copy_plays_out_the_same_as_original(board_class: type[Board], seed: int):
    # The same moves from a copy must lead to the same game
    state   = played_state(board_class, seed)
    clone   = state.copy()
    rng     = Random(seed)

    while not state.finished:
        move = rng.choice(state.legal_moves())

        state.apply(move)
        clone.apply(move)

    assert snapshot(clone) == snapshot(state)


# ---------------------------------------------------------------- undo


def replayed(state: GameState) -> GameState:
    """A fresh game with the same moves as `state` applied, for comparison."""
    fresh = new_state(type(state.board), state.board.height, state.board.width, state.num_players)

    for turn in state.history:
        fresh.apply(turn.move)

    return fresh


def test_undo_reverts_a_plain_move(state: GameState):
    before = snapshot(state)

    state.apply(Move(Coord(0, 0), E))
    state.undo()

    assert snapshot(state) == before


def test_undo_reverts_a_capture(state: GameState):
    state.apply(Move(Coord(0, 0), N))
    before = snapshot(state)

    state.apply(Move(Coord(0, 0), E))   # seat 1 seals off (0, 0)
    state.undo()

    assert snapshot(state)              == before
    assert state.scores                 == [0, 0]
    assert state.board.owner((0, 0))    == -1
    assert state.board.is_in_play((0, 0))
    assert state.current_seat           == 1


def test_undo_reverts_last_two_cells(board_class: type[Board]):
    state   = new_state(board_class, height=1, width=2)
    before  = snapshot(state)

    state.apply(Move(Coord(0, 0), E))
    state.undo()

    assert snapshot(state) == before
    assert not state.finished


def test_undo_restores_legal_moves(board_class: type[Board]):
    state   = played_state(board_class, 0)
    before  = set(state.legal_moves())

    state.apply(state.legal_moves()[0])
    state.undo()

    assert set(state.legal_moves()) == before


@pytest.mark.parametrize("height, width", [(2, 2), (3, 4), (5, 5)])
@pytest.mark.parametrize("seed", range(5))
def test_undo_steps_back_through_a_whole_game(board_class: type[Board], height: int, width: int, seed: int):
    # Play to the end, then undo one move at a time: every step must match the state before that move
    rng         = Random(seed)
    state       = new_state(board_class, height, width)
    snapshots   = [snapshot(state)]

    while not state.finished:
        state.apply(rng.choice(state.legal_moves()))
        snapshots.append(snapshot(state))

    snapshots.pop()

    while snapshots:
        state.undo()

        assert snapshot(state) == snapshots.pop()

    assert snapshot(state) == snapshot(new_state(board_class, height, width))


@pytest.mark.parametrize("seed", range(5))
def test_undo_then_replay_gives_the_same_game(board_class: type[Board], seed: int):
    state   = played_state(board_class, seed)
    moves   = [turn.move for turn in state.history[-5:]]
    end     = snapshot(state)

    for _ in moves:
        state.undo()

    for move in moves:
        state.apply(move)

    assert snapshot(state) == end


@pytest.mark.parametrize("seed", range(10))
def test_mixed_apply_and_undo_like_a_search(board_class: type[Board], seed: int):
    # Searches apply and undo in any order: the state must always match replaying its history
    rng     = Random(seed)
    state   = new_state(board_class, 4, 4)

    for _ in range(200):
        if state.history and (state.finished or rng.random() < 0.4):
            state.undo()
        else:
            state.apply(rng.choice(state.legal_moves()))

        assert snapshot(state) == snapshot(replayed(state))


def test_undo_on_copy_leaves_original(board_class: type[Board]):
    state   = played_state(board_class, 0)
    before  = snapshot(state)
    clone   = state.copy()

    while clone.history:
        clone.undo()

    assert snapshot(state) == before


def test_undo_on_fresh_state_raises_and_leaves_state(state: GameState):
    before = snapshot(state)

    with pytest.raises(IndexError):
        state.undo()

    assert snapshot(state) == before
