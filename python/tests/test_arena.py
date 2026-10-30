from random                      import Random

import pytest

from nagrica.ai                  import Max_N, RandomMove
from nagrica.ai.eval             import CurrentScore, MarginEval
from nagrica.capture             import GreedyDFS
from nagrica.game                import GameState, Move
from nagrica.grid                import Coord, Direction
from nagrica.grid.boards         import LinkedBoard
from arena                       import (
    Contestant, GameResult, is_safe, play_game, random_opening, run_arena, schedule,
    standings, matchups, format_standings, format_matchups,
)
from arena.__main__              import main, parse_args
from nagrica.settings            import GameSettings, LastCellResolution


RANDOM  = Contestant("random",  lambda seed: RandomMove(seed=seed))
RANDOM2 = Contestant("random2", lambda seed: RandomMove(seed=seed))
MAXN    = Contestant("maxn",    lambda seed: Max_N(CurrentScore(), max_depth=1))


# ---------------------------------------------------------------- schedule


def test_schedule_rotates_every_seat():
    lineups = [(round_, tuple(c.name for c in lineup)) for round_, lineup in schedule([RANDOM, MAXN], rounds=2, players_per_game=2)]

    assert lineups == [
        (0, ("random", "maxn")), (0, ("maxn", "random")),
        (1, ("random", "maxn")), (1, ("maxn", "random")),
    ]


def test_schedule_plays_every_group():
    lineups = [lineup for _, lineup in schedule([RANDOM, RANDOM2, MAXN], rounds=1, players_per_game=2)]
    groups  = {frozenset(c.name for c in lineup) for lineup in lineups}

    assert len(lineups) == 3 * 2
    assert groups == {frozenset(pair) for pair in [("random", "random2"), ("random", "maxn"), ("random2", "maxn")]}


def test_schedule_three_players_per_game():
    lineups = [lineup for _, lineup in schedule([RANDOM, RANDOM2, MAXN], rounds=1, players_per_game=3)]

    # Every contestant sits in every seat once
    for seat in range(3):
        assert {lineup[seat].name for lineup in lineups} == {"random", "random2", "maxn"}


# ---------------------------------------------------------------- openings


def new_state(height: int = 4, width: int = 4) -> GameState:
    return GameState(height, width, 2, capture_eval=GreedyDFS, board_class=LinkedBoard)


@pytest.mark.parametrize("seed", range(10))
def test_random_opening_hands_out_nothing(seed: int):
    opening = random_opening(4, 4, 2, moves=5, rng=Random(seed))
    state   = new_state()

    assert len(opening) == 5

    for move in opening:
        state.apply(move)

    assert state.scores == [0, 0]

    # Nor can the next player capture anything
    for reply in state.legal_moves():
        state.apply(reply)
        assert sum(state.scores) == 0
        state.undo()


def test_random_opening_is_reproducible():
    assert random_opening(4, 4, 2, moves=3, rng=Random(1)) == random_opening(4, 4, 2, moves=3, rng=Random(1))


def test_random_opening_stops_without_safe_moves():
    # On a 1x2 board the only move captures, so there is no safe move at all
    assert random_opening(1, 2, 2, moves=3, rng=Random(0)) == ()


def test_is_safe():
    state = new_state(3, 3)

    # A middle wall leaves every cell connected at least twice: nothing to capture
    assert is_safe(state, Move(Coord(1, 1), Direction.NORTH))

    # Walling a corner on one side lets the next player close it
    assert not is_safe(state, Move(Coord(0, 0), Direction.NORTH))


def test_no_safe_move_after_a_corner_is_half_walled():
    state = new_state(3, 3)
    state.apply(Move(Coord(0, 0), Direction.NORTH))

    # Either you close the corner yourself (a capture), or you leave it for the next player
    assert not any(is_safe(state, move) for move in state.legal_moves())


def test_zero_opening_moves():
    assert random_opening(4, 4, 2, moves=0, rng=Random(0)) == ()


# ---------------------------------------------------------------- games


def test_play_game_hands_out_every_cell():
    result = play_game([RANDOM, MAXN], height=3, width=3)

    assert result.lineup        == ("random", "maxn")
    assert sum(result.scores)   == 9
    assert all(times and all(t >= 0 for t in times) for times in result.move_times)


def test_play_game_plays_the_opening_first():
    opening = random_opening(3, 3, 2, moves=3, rng=Random(0))
    result  = play_game([RANDOM, MAXN], height=3, width=3, opening=opening)

    assert result.opening       == opening
    assert sum(result.scores)   == 9

    # The opening moves are not timed: 3x3 has 12 walls, the contestants placed the rest
    assert sum(len(times) for times in result.move_times) <= 12 - len(opening)


def test_play_game_uses_settings():
    # On a 1x2 board the only move splits the last two cells
    current = play_game([RANDOM, MAXN], height=1, width=2, settings=GameSettings(LastCellResolution.CURRENT_PLAYER))
    next_   = play_game([RANDOM, MAXN], height=1, width=2, settings=GameSettings(LastCellResolution.NEXT_PLAYER))

    assert current.scores   == (2, 0)
    assert next_.scores     == (1, 1)


def test_play_game_is_reproducible():
    first   = play_game([RANDOM, RANDOM2], height=3, width=3, seed=7)
    second  = play_game([RANDOM, RANDOM2], height=3, width=3, seed=7)

    assert first.scores == second.scores


def test_run_arena_reports_every_game():
    seen: list[tuple[int, int]] = []

    results = run_arena(
        [RANDOM, MAXN],
        rounds      = 3,
        height      = 3,
        width       = 3,
        on_result   = lambda result, done, total: seen.append((done, total)),
    )

    assert len(results) == 6
    assert seen         == [(done, 6) for done in range(1, 7)]
    assert all(result.group == ("random", "maxn") for result in results)
    assert all(0 < len(result.opening) <= 3 for result in results)   # 3x3 can run out of safe moves


def test_run_arena_shares_openings_within_a_round():
    results = run_arena([RANDOM, RANDOM2, MAXN], rounds=2, height=4, width=4, opening_moves=2)

    # Per group: round 0 (2 seat rotations), then round 1 (2 seat rotations)
    rounds = [
        {result.opening for index, result in enumerate(results) if (index // 2) % 2 == round_}
        for round_ in range(2)
    ]

    assert len(rounds[0]) == 1
    assert len(rounds[1]) == 1
    assert rounds[0] != rounds[1]


def test_run_arena_without_opening():
    results = run_arena([RANDOM, MAXN], rounds=1, height=3, width=3, opening_moves=0)

    assert all(result.opening == () for result in results)


@pytest.mark.parametrize("contestants, players_per_game", [
    ([RANDOM, RANDOM],  2),     # duplicate names
    ([RANDOM, MAXN],    3),     # not enough contestants
    ([RANDOM, MAXN],    1),     # too few players per game
], ids=["duplicate-names", "too-few-contestants", "one-player"])
def test_run_arena_rejects_bad_setup(contestants: list[Contestant], players_per_game: int):
    with pytest.raises(ValueError):
        run_arena(contestants, rounds=1, height=3, width=3, players_per_game=players_per_game)


# ---------------------------------------------------------------- standings


def result(lineup: tuple[str, ...], scores: tuple[int, ...]) -> GameResult:
    return GameResult(
        group       = tuple(sorted(lineup)),
        lineup      = lineup,
        scores      = scores,
        move_times  = tuple((0.001, 0.003) for _ in lineup),
    )


def test_standings_count_wins_draws_losses():
    table = standings([
        result(("a", "b"), (6, 3)),
        result(("b", "a"), (4, 5)),
        result(("a", "b"), (2, 2)),
    ])
    a, b = table

    assert (a.name, a.games, a.wins, a.draws, a.losses) == ("a", 3, 2, 1, 0)
    assert (b.name, b.games, b.wins, b.draws, b.losses) == ("b", 3, 0, 1, 2)
    assert a.score_rate     == pytest.approx(2.5 / 3)
    assert a.points         == 13
    assert a.avg_points     == pytest.approx(13 / 3)
    assert a.point_share    == pytest.approx(13 / 22)


def test_standings_move_times():
    a, _ = standings([result(("a", "b"), (6, 3))])

    assert a.mean_move_time == pytest.approx(0.002)
    assert a.max_move_time  == pytest.approx(0.003)


def test_matchups_split_by_group():
    groups = matchups([
        result(("a", "b"), (6, 3)),
        result(("a", "c"), (1, 8)),
        result(("c", "a"), (8, 1)),
    ])

    assert set(groups) == {("a", "b"), ("a", "c")}

    a, c = groups[("a", "c")]

    assert (a.name, a.losses)   == ("a", 2)
    assert (c.name, c.wins)     == ("c", 2)


def test_format_contains_every_contestant():
    results = [result(("a", "b"), (6, 3))]

    assert all(name in format_standings(standings(results)) for name in ("a", "b"))
    assert "a vs b" in format_matchups(matchups(results))


# ---------------------------------------------------------------- cli


def test_cli_defaults():
    args = parse_args([])

    assert [c.name for c in args.contestants]   == ["random", "maxn"]
    assert args.rounds                          == 10
    assert args.players_per_game                == 2
    assert args.opening                         == 3


def test_cli_margin_and_names():
    args    = parse_args(["-c", "maxn:2:margin(score)", "-c", "maxn:2:margin(score)=deep", "-c", "maxn:2=deep"])
    names   = [c.name for c in args.contestants]
    search  = args.contestants[0].search(0)

    assert names                        == ["maxn:2:margin(score)", "deep", "deep#2"]
    assert type(search.eval_algo)       is MarginEval
    assert type(search.eval_algo.base)  is CurrentScore


def test_cli_contestant_specs():
    args    = parse_args(["-c", "random", "-c", "random", "-c", "MaxN:2:simple"])
    names   = [c.name for c in args.contestants]
    search  = args.contestants[2].search(0)

    assert names                == ["random", "random#2", "maxn:2:simple"]
    assert type(search)         is Max_N
    assert search.max_depth     == 2


@pytest.mark.parametrize("argv", [
    ["-c", "robot", "-c", "random"],            # unknown type
    ["-c", "maxn:0", "-c", "random"],           # zero depth
    ["-c", "maxn:two", "-c", "random"],         # non-number depth
    ["-c", "maxn:2:magic", "-c", "random"],     # unknown evaluation
    ["-c", "random:5", "-c", "maxn"],           # random takes no options
    ["-c", "maxn:2:magic(score)", "-c", "random"], # unknown modifier
    ["-c", "maxn:2:margin", "-c", "random"],    # a modifier is not an evaluation
    ["-o", "-1"],
    ["-c", "random"],                           # one contestant
    ["-n", "3"],                                # more players than contestants
    ["-n", "1"],
], ids=["unknown-type", "zero-depth", "non-number-depth", "unknown-eval", "random-options", "unknown-modifier", "modifier-as-eval", "negative-opening", "one-contestant", "too-many-players", "one-player"])
def test_cli_invalid_arguments_exit(argv: list[str]):
    with pytest.raises(SystemExit):
        parse_args(argv)


def test_cli_runs_an_arena(capsys: pytest.CaptureFixture[str]):
    main(["-c", "random", "-c", "maxn:1", "-r", "2", "--height", "3", "--width", "3", "-q"])

    out = capsys.readouterr().out

    assert "4 games on 3x3" in out
    assert "random vs maxn:1" in out
