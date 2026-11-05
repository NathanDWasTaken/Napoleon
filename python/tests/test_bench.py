import pytest

from nagrica.ai                  import Max_N, RandomMove
from nagrica.ai.eval             import CurrentScore
from nagrica.grid.boards         import BitBoard, LinkedBoard
from nagrica.settings            import GameSettings
from bench                       import Timing, Variant, format_results, playout_workload, record_playout, run_variant, search_workload, variants
from bench.__main__              import main, parse_args


COMMON = dict(height=3, width=3, num_players=2, seed=0, settings=GameSettings(), board_class=LinkedBoard)


def test_record_playout_is_replayable_on_every_board():
    moves = record_playout(3, 3, 2, seed=1, settings=GameSettings(), board_class=LinkedBoard)

    assert moves == record_playout(3, 3, 2, seed=1, settings=GameSettings(), board_class=LinkedBoard)

    for board in (LinkedBoard, BitBoard):
        run_variant(Variant("x", board), playout_workload(games=1, **COMMON), repeat=1, warmup=0)


def test_variants_cross_boards_and_searches():
    boards      = {"linked": LinkedBoard, "bit": BitBoard}
    searches    = {"random": lambda seed: RandomMove(seed=seed), "maxn": lambda seed: Max_N(CurrentScore(), max_depth=1)}

    assert [v.name for v in variants(boards, searches)] == ["random/linked", "maxn/linked", "random/bit", "maxn/bit"]


def test_variants_without_search_use_board_name():
    assert [v.name for v in variants({"linked": LinkedBoard}, {"": None})] == ["linked"]


def test_search_workload_runs():
    variant = Variant("maxn/linked", LinkedBoard, lambda seed: Max_N(CurrentScore(), max_depth=1))
    timing  = run_variant(variant, search_workload(opening=2, positions=2, **COMMON), repeat=2, warmup=0)

    assert len(timing.runs) == 2 and timing.best > 0


def test_search_workload_needs_search():
    run = search_workload(opening=1, positions=1, **COMMON)

    with pytest.raises(AssertionError):
        run(Variant("x", LinkedBoard))


def test_format_results_ranks_fastest_first():
    text = format_results([Timing("slow", (0.2, 0.4)), Timing("fast", (0.1, 0.3))])
    lines = text.splitlines()

    assert lines[2].startswith("fast") and lines[2].endswith("1.00x")
    assert lines[3].startswith("slow") and lines[3].endswith("2.00x")


def test_playout_rejects_ai():
    with pytest.raises(SystemExit):
        parse_args(["playout", "-a", "maxn"])


def test_main_runs(capsys):
    main(["playout", "-q", "-g", "1", "-r", "1", "--height", "3", "--width", "3"])

    out = capsys.readouterr().out

    assert "linked" in out and "bit" in out
