import pytest

from nagrica.__main__            import build_players, main, parse_args
from nagrica.ai                  import RandomMove
from nagrica.players             import ComputerPlayer, HumanPlayer


# ---------------------------------------------------------------- arguments


def test_defaults():
    args = parse_args([])

    assert args.height  == 4
    assert args.width   == 4
    assert args.players == [("human", None), ("human", None)]


def test_player_specs():
    args = parse_args(["-p", "random:Bob", "-p", "HUMAN", "--height", "3", "--width", "5"])

    assert args.players == [("random", "Bob"), ("human", None)]
    assert args.height  == 3
    assert args.width   == 5


@pytest.mark.parametrize("argv", [
    ["-p", "random"],                           # only one player
    ["-p", "robot", "-p", "human"],             # unknown type
    ["--width", "0"],
    ["--height", "-2"],
    ["--height", "four"],
], ids=["one-player", "unknown-type", "zero-width", "negative-height", "non-number"])
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


def test_computer_players_get_their_own_search():
    first, second = build_players([("random", None), ("random", None)])

    assert first.search_algo is not second.search_algo


# ---------------------------------------------------------------- main


def test_main_plays_a_random_game(capsys: pytest.CaptureFixture[str]):
    main(["-p", "random:Ann", "-p", "random:Bob", "--height", "3", "--width", "3"])

    output = capsys.readouterr().out

    assert "Ann: "  in output
    assert "Bob: "  in output
    assert "Winner: " in output or "Draw between: " in output


def test_main_handles_abort(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]):
    monkeypatch.setattr("builtins.input", lambda prompt="": "exit")

    main(["-p", "human", "-p", "random"])

    assert "Game aborted." in capsys.readouterr().out
