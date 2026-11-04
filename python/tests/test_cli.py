import io
import sys

from pathlib                    import Path

import pytest

from nagrica.__main__            import build_players, main, parse_args
from nagrica.ai                  import Max_N, RandomMove
from nagrica.ai.eval             import MarginEval
from nagrica.players             import ComputerPlayer, HumanPlayer
from nagrica.settings            import LastCellResolution
from nagrica.cli                 import BOARDS, board_class, game_settings
from nagrica.grid                import Coord, Direction, Edge
from nagrica.grid.boards         import BitBoard, LinkedBoard
from nagrica.ui                  import parse_record


# ---------------------------------------------------------------- arguments


def test_defaults():
    args = parse_args([])

    assert args.height      == 4
    assert args.width       == 4
    assert args.players     == [("human", None), ("human", None)]
    assert game_settings(args).LASTCELLRESOLUTION == LastCellResolution.NEXT_PLAYER
    assert board_class(args)    is LinkedBoard


@pytest.mark.parametrize("name, cls", [("linked", LinkedBoard), ("bit", BitBoard)])
def test_board_option(name: str, cls: type):
    assert board_class(parse_args(["--board", name])) is cls


def test_player_specs():
    args = parse_args([
        "-p", "random=Bob", "-p", "HUMAN", "-p", "maxn:2:margin(score)=Deep Blue",
        "--height", "3", "--width", "5", "--last-cell", "current",
    ])

    assert args.players == [("random", "Bob"), ("human", None), ("maxn:2:margin(score)", "Deep Blue")]
    assert args.height  == 3
    assert args.width   == 5
    assert game_settings(args).LASTCELLRESOLUTION == LastCellResolution.CURRENT_PLAYER


@pytest.mark.parametrize("argv", [
    ["-p", "random"],                           # only one player
    ["-p", "robot", "-p", "human"],             # unknown type
    ["-p", "human:Alice", "-p", "human"],       # names use =, not :
    ["-p", "maxn:0", "-p", "human"],            # zero depth
    ["-p", "maxn:2:magic", "-p", "human"],      # unknown evaluation
    ["--width", "0"],
    ["--height", "-2"],
    ["--height", "four"],
    ["--last-cell", "first"],
    ["--board", "array"],
], ids=["one-player", "unknown-type", "human-options", "zero-depth", "unknown-eval", "zero-width", "negative-height", "non-number", "unknown-last-cell", "unknown-board"])
def test_invalid_arguments_exit(argv: list[str]):
    with pytest.raises(SystemExit):
        parse_args(argv)


# ---------------------------------------------------------------- players


def test_build_players():
    players = build_players([("human", "Alice"), ("random", None)])

    assert type(players[0]) is HumanPlayer
    assert type(players[1]) is ComputerPlayer
    assert type(players[1].search_algo) is RandomMove
    assert [p.name for p in players] == ["Alice", "Player 2"]
    assert [p.seat for p in players] == [0, 1]


def test_maxn_options():
    player, default = build_players([("maxn:5:margin(score)", None), ("maxn", None)])

    assert type(player.search_algo)             is Max_N
    assert player.search_algo.max_depth         == 5
    assert type(player.search_algo.eval_algo)   is MarginEval
    assert default.search_algo.max_depth        == 3


def test_computer_players_get_their_own_search():
    first, second = build_players([("random", None), ("random", None)])

    assert first.search_algo is not second.search_algo


# ---------------------------------------------------------------- main


def test_main_plays_a_random_game(capsys: pytest.CaptureFixture[str]):
    main(["-p", "random=Ann", "-p", "random=Bob", "--height", "3", "--width", "3"])

    output = capsys.readouterr().out

    assert "Ann: "  in output
    assert "Bob: "  in output
    assert "Winner: " in output or "Draw between: " in output


def test_main_uses_board_option(monkeypatch: pytest.MonkeyPatch):
    used: list[type] = []

    class SpyBoard(LinkedBoard):
        def __init__(self, height: int, width: int) -> None:
            used.append(type(self))
            super().__init__(height, width)

    monkeypatch.setitem(BOARDS, "spy", SpyBoard)

    main(["-p", "random", "-p", "random", "--height", "2", "--width", "2", "--board", "spy"])

    assert used == [SpyBoard]


def test_main_handles_abort(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr("builtins.input", lambda prompt="": "exit")

    main(["-p", "human", "-p", "random"])

    assert "Game aborted." in capsys.readouterr().out


# ---------------------------------------------------------------- record and replay


class FakeStdin(io.StringIO):
    def __init__(self, text: str = "", tty: bool = False) -> None:
        super().__init__(text)
        self.tty = tty

    def isatty(self) -> bool:
        return self.tty


def scores_line(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.startswith(("A: ", "B: "))]


def test_record_then_replay_gives_the_same_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    path = tmp_path / "game.ngn"

    main(["-p", "random=A", "-p", "maxn:1=B", "--height", "3", "--width", "3", "--last-cell", "current", "--record", str(path)])

    played = capsys.readouterr().out
    record = parse_record(path.read_text(encoding="utf-8"))

    assert record.players       == [("A", "random"), ("B", "maxn:1:margin(score)")]
    assert (record.height, record.width, record.last_cell) == (3, 3, "current")
    assert record.result        != "*"
    assert f"Game recorded to {path}" in played

    monkeypatch.setattr(sys, "stdin", FakeStdin())
    main(["--replay", str(path)])

    replayed = capsys.readouterr().out

    assert scores_line(replayed) == scores_line(played)
    assert record.result == "-".join(line.split(": ")[1] for line in scores_line(played))
    assert "1. A: " in replayed


def test_aborted_game_is_recorded_as_unfinished(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    path    = tmp_path / "game.ngn"
    answers = iter(["0 0 N", "exit"])

    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    main(["-p", "human", "-p", "human", "--height", "2", "--width", "2", "--record", str(path)])

    record = parse_record(path.read_text(encoding="utf-8"))

    assert record.result    == "*"
    assert record.moves     == [Edge(Coord(0, 0), Direction.NORTH)]


def test_replay_waits_for_enter_and_can_quit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    path = tmp_path / "game.ngn"
    path.write_text('[Height "2"]\n[Width "2"]\n[LastCell "next"]\n[Player1 "A"]\n[Player2 "B"]\n\n1. a1N b1N 2. a1E *', encoding="utf-8")

    answers = iter(["", "q"])
    monkeypatch.setattr(sys, "stdin", FakeStdin(tty=True))
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    main(["--replay", str(path)])

    out = capsys.readouterr().out

    assert "1. A: a1N" in out
    assert "B: b1N" not in out


def test_replay_of_unfinished_game(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    path = tmp_path / "game.ngn"
    path.write_text('[Height "2"]\n[Width "2"]\n[LastCell "next"]\n[Player1 "A"]\n[Player2 "B"]\n\n1. a1N b1N *', encoding="utf-8")

    monkeypatch.setattr(sys, "stdin", FakeStdin())
    main(["--replay", str(path)])

    out = capsys.readouterr().out

    assert "1. B: b1N" in out
    assert "The record ends before the game is finished." in out


@pytest.mark.parametrize("content, message", [
    (None,                                                                                          "Can't replay"),
    ('[Height "2"]\n[Width "2"]\n[LastCell "next"]\n[Player1 "A"]\n[Player2 "B"]\n\n1. a1N a1N',    "Move 1. a1N by B is not legal"),
    ('[Height "2"]\n[Width "2"]\n[LastCell "maybe"]\n[Player1 "A"]\n[Player2 "B"]',                 "unknown LastCell"),
    ('[Height "2"]\n[Player1 "A"]\n[Player2 "B"]',                                                  "missing tag"),
], ids=["missing-file", "illegal-move", "unknown-last-cell", "missing-tag"])
def test_replay_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: str | None, message: str):
    path = tmp_path / "game.ngn"

    if content is not None:
        path.write_text(content, encoding="utf-8")

    monkeypatch.setattr(sys, "stdin", FakeStdin())

    with pytest.raises(SystemExit) as exit_info:
        main(["--replay", str(path)])

    assert message in str(exit_info.value.code)
