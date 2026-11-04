"""
Ownership tracking in `CompleteGameState`. The game rules themselves are
covered by `test_game_state.py`; here they only need to match `BasicGameState`.
"""
from random         import Random

import pytest

from nagrica.game       import CompleteGameState, BasicGameState
from nagrica.grid       import Edge, Board, Coord, Direction
from nagrica.settings   import GameSettings, LastCellResolution


N, E, S, W = Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST


CURRENT_PLAYER  = GameSettings(LastCellResolution.CURRENT_PLAYER)
NEXT_PLAYER     = GameSettings(LastCellResolution.NEXT_PLAYER)


def new_state[T: BasicGameState](
    board_class:    type[Board],
    height:         int             = 3,
    width:          int             = 3,
    num_players:    int             = 2,
    settings:       GameSettings    = GameSettings(),
    state_class:    type[T]         = CompleteGameState,
) -> T:
    return state_class(
        height,
        width,
        num_players,
        board_class     = board_class,
        settings        = settings,
    )


@pytest.fixture(params=[CURRENT_PLAYER, NEXT_PLAYER], ids=lambda settings: settings.LASTCELLRESOLUTION.name)
def settings(request: pytest.FixtureRequest) -> GameSettings:
    return request.param


@pytest.fixture
def state(board_class: type[Board], settings: GameSettings) -> CompleteGameState:
    return new_state(board_class, settings=settings)


def play_random(state: BasicGameState, rng: Random, moves: int | None = None):
    """Play random legal moves, until the game ends or `moves` have been played."""
    while not state.finished and moves != 0:
        state.apply(rng.choice(state.legal_moves()))

        if moves is not None:
            moves -= 1


def snapshot(state: CompleteGameState) -> tuple:
    """Everything observable about a complete game state, ownership included."""
    board   = state.board
    coords  = [Coord(x, y) for y in range(board.height) for x in range(board.width)]

    return (
        frozenset((coord, direction) for coord in coords for direction in Direction if board.connects(Edge(coord, direction))),
        frozenset(board.in_play),
        tuple(state.scores),
        tuple(state.history),
        state.current_seat,
        dict(state.captured),
        dict(state.placed),
    )


def expected_ownership(state: BasicGameState) -> tuple[dict[Coord, int], dict[Edge, int]]:
    """Ownership derived from the history alone, to compare against what is tracked."""
    captured:   dict[Coord, int]    = {}
    placed:     dict[Edge, int]     = {}

    for turn in state.history:
        if turn.wall is not None:
            placed[turn.wall] = turn.player_seat

        for coord in turn.capture.coords:
            captured[coord] = turn.player_seat

    return captured, placed


# ---------------------------------------------------------------- initial state


def test_is_a_basic_game_state(state: CompleteGameState):
    # Rules and engines are written against BasicGameState, so a complete one must work as one
    assert isinstance(state, BasicGameState)


def test_nothing_is_owned_at_the_start(state: CompleteGameState):
    assert state.captured   == {}
    assert state.placed     == {}


# ---------------------------------------------------------------- walls


def test_apply_records_wall_for_the_mover(state: CompleteGameState):
    state.apply(Edge(Coord(0, 0), E))   # seat 0
    state.apply(Edge(Coord(1, 1), N))   # seat 1

    assert state.placed == {
        Edge(Coord(0, 0), E): 0,
        Edge(Coord(1, 1), N): 1,
    }


def test_plain_move_captures_nothing(state: CompleteGameState):
    state.apply(Edge(Coord(0, 0), E))

    assert state.captured == {}


# ---------------------------------------------------------------- captures


def test_capture_is_owned_by_the_mover(state: CompleteGameState):
    state.apply(Edge(Coord(0, 0), N))   # seat 0, no capture
    state.apply(Edge(Coord(0, 0), E))   # seat 1, seals off (0, 0)

    assert state.captured == {Coord(0, 0): 1}


def test_last_two_cells_are_owned_by_the_mover(board_class: type[Board]):
    state = new_state(board_class, height=1, width=2, settings=CURRENT_PLAYER)

    state.apply(Edge(Coord(0, 0), E))

    assert state.captured == {Coord(0, 0): 0, Coord(1, 0): 0}


def test_last_cell_is_owned_by_the_next_player(board_class: type[Board]):
    state = new_state(board_class, height=1, width=2, settings=NEXT_PLAYER)

    state.apply(Edge(Coord(0, 0), E))

    mover, last = state.history

    assert state.captured == (
        {coord: 0 for coord in mover.capture.coords}
            |
        {coord: 1 for coord in last.capture.coords}
    )

    # The last cell's turn has no wall, so it places nothing
    assert state.placed == {Edge(Coord(0, 0), E): 0}


# ---------------------------------------------------------------- full games


@pytest.mark.parametrize("height, width", [(2, 2), (3, 4), (5, 5)])
@pytest.mark.parametrize("seed", range(5))
def test_random_game_owns_every_cell(board_class: type[Board], settings: GameSettings, height: int, width: int, seed: int):
    state = new_state(board_class, height, width, settings=settings)

    play_random(state, Random(seed))

    assert set(state.captured) == {Coord(x, y) for y in range(height) for x in range(width)}

    for seat, score in enumerate(state.scores):
        assert list(state.captured.values()).count(seat) == score


@pytest.mark.parametrize("seed", range(5))
def test_ownership_matches_history(board_class: type[Board], settings: GameSettings, seed: int):
    state = new_state(board_class, 4, 4, settings=settings)

    play_random(state, Random(seed))

    assert (state.captured, state.placed) == expected_ownership(state)


@pytest.mark.parametrize("seed", range(5))
def test_plays_the_same_game_as_basic_state(board_class: type[Board], settings: GameSettings, seed: int):
    # Ownership tracking must not change the rules
    rng         = Random(seed)
    complete    = new_state(board_class, 4, 4, settings=settings)
    simple      = new_state(board_class, 4, 4, settings=settings, state_class=BasicGameState)

    while not complete.finished:
        move = rng.choice(complete.legal_moves())

        complete.apply(move)
        simple.apply(move)

    assert complete.history == simple.history
    assert complete.scores  == simple.scores


# ---------------------------------------------------------------- undo


def test_undo_reverts_a_plain_move(state: CompleteGameState):
    state.apply(Edge(Coord(0, 0), E))
    state.undo()

    assert state.placed     == {}
    assert state.captured   == {}


def test_undo_reverts_a_capture(state: CompleteGameState):
    state.apply(Edge(Coord(0, 0), N))
    before = snapshot(state)

    state.apply(Edge(Coord(0, 0), E))   # seat 1 seals off (0, 0)
    state.undo()

    assert snapshot(state)  == before
    assert state.captured   == {}
    assert state.placed     == {Edge(Coord(0, 0), N): 0}


def test_undo_reverts_last_two_cells(board_class: type[Board], settings: GameSettings):
    state   = new_state(board_class, height=1, width=2, settings=settings)
    before  = snapshot(state)

    state.apply(Edge(Coord(0, 0), E))
    state.undo()

    assert snapshot(state) == before


@pytest.mark.parametrize("height, width", [(2, 2), (3, 4), (5, 5)])
@pytest.mark.parametrize("seed", range(5))
def test_undo_steps_back_through_a_whole_game(board_class: type[Board], settings: GameSettings, height: int, width: int, seed: int):
    rng         = Random(seed)
    state       = new_state(board_class, height, width, settings=settings)
    snapshots   = [snapshot(state)]

    while not state.finished:
        state.apply(rng.choice(state.legal_moves()))
        snapshots.append(snapshot(state))

    snapshots.pop()

    while snapshots:
        state.undo()

        assert snapshot(state) == snapshots.pop()


@pytest.mark.parametrize("seed", range(10))
def test_mixed_apply_and_undo_like_a_search(board_class: type[Board], settings: GameSettings, seed: int):
    # Ownership must always match what the history says, whatever the order of apply and undo
    rng     = Random(seed)
    state   = new_state(board_class, 4, 4, settings=settings)

    for _ in range(200):
        if state.history and (state.finished or rng.random() < 0.4):
            state.undo()
        else:
            state.apply(rng.choice(state.legal_moves()))

        assert (state.captured, state.placed) == expected_ownership(state)


# ---------------------------------------------------------------- copy


def played_state(board_class: type[Board], settings: GameSettings, seed: int, moves: int = 10) -> CompleteGameState:
    """A 4x4 game, part way through, with some captures."""
    state = new_state(board_class, 4, 4, settings=settings)

    play_random(state, Random(seed), moves)

    return state


def test_copy_is_same_class(state: CompleteGameState):
    assert type(state.copy()) is CompleteGameState


def test_copy_has_every_field(board_class: type[Board], settings: GameSettings):
    state = played_state(board_class, settings, 0)

    assert vars(state.copy()).keys() == vars(state).keys()


def test_copy_does_not_share_ownership(state: CompleteGameState):
    clone = state.copy()

    assert clone.captured   is not state.captured
    assert clone.placed     is not state.placed


@pytest.mark.parametrize("seed", range(5))
def test_copy_matches_mid_game(board_class: type[Board], settings: GameSettings, seed: int):
    state = played_state(board_class, settings, seed)

    assert snapshot(state.copy()) == snapshot(state)


@pytest.mark.parametrize("seed", range(3))
def test_playing_on_copy_leaves_original(board_class: type[Board], settings: GameSettings, seed: int):
    state   = played_state(board_class, settings, seed)
    before  = snapshot(state)
    clone   = state.copy()

    play_random(clone, Random(seed))

    assert snapshot(state) == before


@pytest.mark.parametrize("seed", range(3))
def test_undoing_on_copy_leaves_original(board_class: type[Board], settings: GameSettings, seed: int):
    state   = played_state(board_class, settings, seed)
    before  = snapshot(state)
    clone   = state.copy()

    while clone.history:
        clone.undo()

    assert snapshot(state) == before


# ---------------------------------------------------------------- to_simple


def basic_snapshot(state: BasicGameState) -> tuple:
    """Everything a `BasicGameState` holds, so it can be compared with a complete one."""
    board   = state.board
    coords  = [Coord(x, y) for y in range(board.height) for x in range(board.width)]

    return (
        frozenset((coord, direction) for coord in coords for direction in Direction if board.connects(Edge(coord, direction))),
        frozenset(board.in_play),
        tuple(state.scores),
        tuple(state.history),
        state.current_seat,
        state.finished,
    )


def test_to_simple_gives_a_plain_basic_state(state: CompleteGameState):
    # Engines get the simple version, so no ownership is carried along
    assert type(state.to_simple()) is BasicGameState


def test_to_simple_has_the_fields_of_a_basic_state(board_class: type[Board], settings: GameSettings):
    complete    = played_state(board_class, settings, 0)
    simple      = new_state(board_class, 4, 4, settings=settings, state_class=BasicGameState)

    assert vars(complete.to_simple()).keys() == vars(simple).keys()


def test_to_simple_of_fresh_state_matches(state: CompleteGameState):
    assert basic_snapshot(state.to_simple()) == basic_snapshot(state)


@pytest.mark.parametrize("seed", range(5))
def test_to_simple_matches_mid_game(board_class: type[Board], settings: GameSettings, seed: int):
    state = played_state(board_class, settings, seed)

    assert basic_snapshot(state.to_simple()) == basic_snapshot(state)


def test_to_simple_keeps_board_class_and_settings(board_class: type[Board], settings: GameSettings):
    simple = played_state(board_class, settings, 0).to_simple()

    assert type(simple.board)   is board_class
    assert simple._settings     is settings
    assert simple.num_players   == 2


def test_to_simple_does_not_share_mutable_parts(state: CompleteGameState):
    simple = state.to_simple()

    assert simple.board     is not state.board
    assert simple.scores    is not state.scores
    assert simple.history   is not state.history


def test_to_simple_leaves_original_unchanged(board_class: type[Board], settings: GameSettings):
    state   = played_state(board_class, settings, 0)
    before  = snapshot(state)

    state.to_simple()

    assert snapshot(state) == before


@pytest.mark.parametrize("seed", range(3))
def test_playing_on_simple_leaves_original(board_class: type[Board], settings: GameSettings, seed: int):
    state   = played_state(board_class, settings, seed)
    before  = snapshot(state)
    simple  = state.to_simple()

    play_random(simple, Random(seed))

    assert snapshot(state) == before


@pytest.mark.parametrize("seed", range(3))
def test_undoing_on_simple_leaves_original(board_class: type[Board], settings: GameSettings, seed: int):
    state   = played_state(board_class, settings, seed)
    before  = snapshot(state)
    simple  = state.to_simple()

    while simple.history:
        simple.undo()

    assert snapshot(state) == before


@pytest.mark.parametrize("seed", range(3))
def test_playing_on_original_leaves_simple(board_class: type[Board], settings: GameSettings, seed: int):
    state   = played_state(board_class, settings, seed)
    simple  = state.to_simple()
    before  = basic_snapshot(simple)

    play_random(state, Random(seed))

    assert basic_snapshot(simple) == before


@pytest.mark.parametrize("seed", range(3))
def test_simple_plays_out_the_same_as_original(board_class: type[Board], settings: GameSettings, seed: int):
    # Searching on the simple state must follow the same game as the match
    state   = played_state(board_class, settings, seed)
    simple  = state.to_simple()
    rng     = Random(seed)

    while not state.finished:
        move = rng.choice(state.legal_moves())

        state.apply(move)
        simple.apply(move)

    assert basic_snapshot(simple) == basic_snapshot(state)


@pytest.mark.parametrize("seed", range(3))
def test_simple_undoes_back_to_the_start(board_class: type[Board], settings: GameSettings, seed: int):
    # Searches undo past the point they were handed, so the history must come along intact
    simple = played_state(board_class, settings, seed).to_simple()

    while simple.history:
        simple.undo()

    fresh = new_state(board_class, 4, 4, settings=settings, state_class=BasicGameState)

    assert basic_snapshot(simple) == basic_snapshot(fresh)
