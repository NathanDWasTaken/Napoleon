import pytest

from nagrica.__main__            import build_players, main, parse_args
from nagrica.ai                  import Max_N, RandomMove
from nagrica.ai.eval             import MarginEval
from nagrica.players             import ComputerPlayer, HumanPlayer
from nagrica.settings            import LastCellResolution
from nagrica.cli                 import game_settings


# ---------------------------------------------------------------- arguments


def test_defaults():
    args = parse_args([])

    assert args.height      == 4
    assert args.width       == 4
    assert args.players     == [("human", None), ("human", None)]
    assert game_settings(args).LASTCELLRESOLUTION == LastCellResolution.NEXT_PLAYER


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
], ids=["one-player", "unknown-type", "human-options", "zero-depth", "unknown-eval", "zero-width", "negative-height", "non-number", "unknown-last-cell"])
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


def test_main_handles_abort(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr("builtins.input", lambda prompt="": "exit")

    main(["-p", "human", "-p", "random"])

    assert "Game aborted." in capsys.readouterr().out
