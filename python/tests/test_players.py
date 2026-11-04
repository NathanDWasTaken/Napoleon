from collections.abc    import Iterator

import pytest

from nagrica.game               import BasicGameState, CompleteGameState
from nagrica.grid.boards        import LinkedBoard
from nagrica.grid               import Edge, Coord, Direction
from nagrica.ai                 import SearchAlgorithm
from nagrica.players            import ComputerPlayer, HumanPlayer
from nagrica.players.exceptions import InvalidInputPattern


N, E, S, W = Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST
HEIGHT, WIDTH = 5, 4


def new_state(height: int = 3, width: int = 3) -> CompleteGameState:
    return CompleteGameState(height, width, 2, board_class=LinkedBoard)


def feed_input(monkeypatch: pytest.MonkeyPatch, *lines: str) -> None:
    """Answer each `input()` call with the next line."""
    answers: Iterator[str] = iter(lines)

    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))


@pytest.fixture
def human() -> HumanPlayer:
    return HumanPlayer("Alice", 0)


# ---------------------------------------------------------------- HumanPlayer input parsing


@pytest.mark.parametrize("text, move", [
    ("0 1 N",           Edge(Coord(0, 1),  N)),
    ("0 1 n",           Edge(Coord(0, 1),  N)),
    ("2,3 W",           Edge(Coord(2, 3),  W)),
    ("(0, 1) E",        Edge(Coord(0, 1),  E)),
    ("12 3 S",          Edge(Coord(12, 3), S)),
    ("0 1 0 2",         Edge(Coord(0, 1),  N)),
    ("1 1 0 1",         Edge(Coord(1, 1),  W)),
    ("(2,3) (2,2)",     Edge(Coord(2, 3),  S)),
    ("-1 1 W",          Edge(Coord(3, 1),  W)),
    ("0 -3 N",          Edge(Coord(0, 2),  N)),
    ("-1 -3 -2 -3",     Edge(Coord(3, 2),  W)),
])
def test_parse_valid_input(human: HumanPlayer, text: str, move: Edge):
    assert human._parse_input(text, height=HEIGHT, width=WIDTH) == move


@pytest.mark.parametrize("text", [
    "",
    "hello",
    "0 N",
    "0 1 X",
    "0 0 2 2",      # not neighbours
    "0 0 0 0",      # same cell
], ids=["empty", "word", "missing-coord", "bad-direction", "not-neighbours", "same-cell"])
def test_parse_invalid_input_raises(human: HumanPlayer, text: str):
    with pytest.raises(InvalidInputPattern):
        human._parse_input(text, height=HEIGHT, width=WIDTH)


# ---------------------------------------------------------------- HumanPlayer turn loop


def test_make_move_returns_parsed_move(human: HumanPlayer, monkeypatch: pytest.MonkeyPatch):
    feed_input(monkeypatch, "0 0 N")

    assert human.make_move(new_state()) == Edge(Coord(0, 0), N)


def test_make_move_asks_again_after_bad_input(human: HumanPlayer, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    feed_input(monkeypatch, "help", "garbage", "0 0 S", "0 0 N")

    assert human.make_move(new_state()) == Edge(Coord(0, 0), N)

    output = capsys.readouterr().out

    assert "The goal of the game"   in output
    assert "Could not parse input"  in output
    assert "Move is Illegal!"       in output


def test_make_move_random_returns_legal_move(human: HumanPlayer, monkeypatch: pytest.MonkeyPatch):
    state = new_state()
    feed_input(monkeypatch, "random")

    assert state.is_legal(human.make_move(state))


def test_make_move_exit_aborts(human: HumanPlayer, monkeypatch: pytest.MonkeyPatch):
    feed_input(monkeypatch, "exit")

    with pytest.raises(KeyboardInterrupt):
        human.make_move(new_state())


# ---------------------------------------------------------------- ComputerPlayer


class StubSearch(SearchAlgorithm):
    """Returns a fixed move and records what it was asked."""

    def __init__(self, move: Edge) -> None:
        self.move   = move
        self.calls: list[BasicGameState] = []

    def select_move(self, gameState: BasicGameState) -> Edge:
        self.calls.append(gameState)

        return self.move


class MeddlingSearch(SearchAlgorithm):
    """Plays out the rest of the game on the state it is given, like a deep search could."""

    def __init__(self) -> None:
        pass

    def select_move(self, gameState: BasicGameState) -> Edge:
        move = gameState.legal_moves()[0]

        while not gameState.finished:
            gameState.apply(gameState.legal_moves()[0])

        return move


def played_state(moves: int = 6) -> CompleteGameState:
    state = new_state(4, 4)

    for _ in range(moves):
        state.apply(state.legal_moves()[0])

    return state


def test_computer_player_returns_the_search_move():
    move    = Edge(Coord(0, 0), N)
    player  = ComputerPlayer("Bot", 0, search_algo=StubSearch(move))

    assert player.make_move(new_state()) == move


def test_computer_player_searches_a_basic_state():
    # Engines skip ownership tracking, so they must not be handed the complete state
    search  = StubSearch(Edge(Coord(0, 0), N))
    player  = ComputerPlayer("Bot", 1, search_algo=search)

    player.make_move(played_state())

    assert len(search.calls) == 1
    assert type(search.calls[0]) is BasicGameState


def test_computer_player_searches_the_same_position():
    search  = StubSearch(Edge(Coord(0, 0), N))
    player  = ComputerPlayer("Bot", 1, search_algo=search)
    state   = played_state()

    player.make_move(state)

    searched = search.calls[0]

    assert searched.history                 == state.history
    assert searched.scores                  == state.scores
    assert searched.current_seat            == state.current_seat
    assert set(searched.board.in_play)      == set(state.board.in_play)
    assert set(searched.legal_moves())      == set(state.legal_moves())


def test_computer_player_search_leaves_the_given_state():
    player  = ComputerPlayer("Bot", 0, search_algo=MeddlingSearch())
    state   = played_state()
    history = list(state.history)
    placed  = dict(state.placed)

    player.make_move(state)

    assert state.history    == history
    assert state.placed     == placed
    assert not state.finished
