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
