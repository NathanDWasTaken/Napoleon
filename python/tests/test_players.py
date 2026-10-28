from collections.abc    import Iterator

import pytest

from nagrica.capture             import GreedyDFS
from nagrica.game                import GameState, Move
from nagrica.grid.boards         import LinkedBoard
from nagrica.grid.coord          import Coord
from nagrica.grid.direction      import Direction
from nagrica.ai                  import SearchAlgorithm
from nagrica.players             import ComputerPlayer, HumanPlayer
from nagrica.players.exceptions  import InvalidInputPattern


N, E, S, W = Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST
HEIGHT, WIDTH = 5, 4


def new_state(height: int = 3, width: int = 3) -> GameState:
    return GameState(height, width, 2, capture_eval=GreedyDFS, board_class=LinkedBoard)


def feed_input(monkeypatch: pytest.MonkeyPatch, *lines: str) -> None:
    """Answer each `input()` call with the next line."""
    answers: Iterator[str] = iter(lines)

    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))


@pytest.fixture
def human() -> HumanPlayer:
    return HumanPlayer("Alice", 0)


# ---------------------------------------------------------------- HumanPlayer input parsing


@pytest.mark.parametrize("text, move", [
    ("0 1 N",           Move(Coord(0, 1),  N)),
    ("0 1 n",           Move(Coord(0, 1),  N)),
    ("2,3 W",           Move(Coord(2, 3),  W)),
    ("(0, 1) E",        Move(Coord(0, 1),  E)),
    ("12 3 S",          Move(Coord(12, 3), S)),
    ("0 1 0 2",         Move(Coord(0, 1),  N)),
    ("1 1 0 1",         Move(Coord(1, 1),  W)),
    ("(2,3) (2,2)",     Move(Coord(2, 3),  S)),
    ("-1 1 W",          Move(Coord(3, 1),  W)),
    ("0 -3 N",          Move(Coord(0, 2),  N)),
    ("-1 -3 -2 -3",     Move(Coord(3, 2),  W)),
])
def test_parse_valid_input(human: HumanPlayer, text: str, move: Move):
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

    assert human.make_move(new_state()) == Move(Coord(0, 0), N)


def test_make_move_asks_again_after_bad_input(human: HumanPlayer, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    feed_input(monkeypatch, "help", "garbage", "0 0 S", "0 0 N")

    assert human.make_move(new_state()) == Move(Coord(0, 0), N)

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

    def __init__(self, move: Move) -> None:
        self.move   = move
        self.calls: list[GameState] = []

    def select_move(self, gameState: GameState) -> Move:
        self.calls.append(gameState)

        return self.move


def test_computer_player_returns_the_search_move():
    move    = Move(Coord(0, 0), N)
    player  = ComputerPlayer("Bot", 0, search_algo=StubSearch(move))

    assert player.make_move(new_state()) == move


def test_computer_player_passes_the_state():
    search  = StubSearch(Move(Coord(0, 0), N))
    player  = ComputerPlayer("Bot", 1, search_algo=search)
    state   = new_state()

    player.make_move(state)

    assert search.calls == [state]
