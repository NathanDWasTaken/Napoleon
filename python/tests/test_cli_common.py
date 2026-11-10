from argparse                    import ArgumentTypeError

import pytest

from nagrica.ai                  import CurrentScore, Max_N, RandomMove, SimpleEval
from nagrica.ai.eval             import MarginEval
from nagrica.cli                 import full_ai_spec, non_negative_int, parse_ai, parse_evaluation, positive_int, split_name


# ---------------------------------------------------------------- numbers


def test_numbers():
    assert positive_int("3")        == 3
    assert non_negative_int("0")    == 0


@pytest.mark.parametrize("parse, value", [
    (positive_int,      "0"),
    (positive_int,      "two"),
    (non_negative_int,  "-1"),
])
def test_bad_numbers(parse, value: str):
    with pytest.raises(ArgumentTypeError):
        parse(value)


# ---------------------------------------------------------------- evaluations


def test_plain_evaluation():
    assert type(parse_evaluation("score")())    is CurrentScore
    assert type(parse_evaluation("simple")())   is SimpleEval


def test_wrapped_evaluation():
    evaluation = parse_evaluation("margin(simple)")()

    assert type(evaluation)         is MarginEval
    assert type(evaluation.base)    is SimpleEval


def test_nested_evaluation():
    evaluation = parse_evaluation("margin(margin(score))")()

    assert type(evaluation.base)        is MarginEval
    assert type(evaluation.base.base)   is CurrentScore


def test_evaluations_are_fresh_instances():
    build = parse_evaluation("margin(score)")

    assert build() is not build()


@pytest.mark.parametrize("spec", [
    "magic",                # unknown evaluation
    "margin",               # a modifier on its own
    "magic(score)",         # unknown modifier
    "margin(score",         # missing bracket
    "margin(magic)",        # unknown inner evaluation
    "margin()",
], ids=["unknown", "bare-modifier", "unknown-modifier", "missing-bracket", "unknown-inner", "empty"])
def test_bad_evaluations(spec: str):
    with pytest.raises(ArgumentTypeError):
        parse_evaluation(spec)


# ---------------------------------------------------------------- AIs


def test_parse_ai():
    random  = parse_ai("random")(5)
    maxn    = parse_ai("maxn:2:margin(score)")(None)

    assert type(random)             is RandomMove
    assert type(maxn)               is Max_N
    assert maxn.max_depth           == 2
    assert type(maxn.eval_algo)     is MarginEval


def test_parse_ai_defaults():
    maxn = parse_ai("maxn")(None)

    assert maxn.max_depth               == 3
    assert type(maxn.eval_algo)         is MarginEval
    assert type(maxn.eval_algo.base)    is CurrentScore


def test_parse_ai_time_limit_and_unlimited_depth():
    maxn = parse_ai("maxn:inf:score:2.5")(None)

    assert maxn.max_depth == float("inf")
    assert maxn.max_time  == 2.5
    assert parse_ai("maxn:3")(None).max_time == float("inf")


@pytest.mark.parametrize("spec", [
    "robot",
    "random:5",
    "maxn:0",
    "maxn:two",
    "maxn:2:score:extra",
    "maxn:2:score:0",
    "maxn:2:score:fast",
    "maxn:2:score:1:more",
], ids=["unknown-type", "random-options", "zero-depth", "non-number-depth", "non-number-time", "zero-time", "word-time", "too-many-options"])
def test_bad_ais(spec: str):
    with pytest.raises(ArgumentTypeError):
        parse_ai(spec)


# ---------------------------------------------------------------- names


@pytest.mark.parametrize("value, expected", [
    ("random",                  ("random", None)),
    ("Random=Bob",              ("random", "Bob")),
    ("maxn:3:Margin(score)=X",  ("maxn:3:margin(score)", "X")),
    ("human=",                  ("human", None)),
])
def test_split_name(value: str, expected: tuple[str, str | None]):
    assert split_name(value) == expected


@pytest.mark.parametrize("spec, full", [
    ("random",                  "random"),
    ("maxn",                    "maxn:3:margin(score)"),
    ("maxn:5",                  "maxn:5:margin(score)"),
    ("maxn:2:margin(simple)",   "maxn:2:margin(simple)"),
    ("maxn:INF:score:2",        "maxn:inf:score:2"),
])
def test_full_ai_spec_fills_in_defaults(spec: str, full: str):
    assert full_ai_spec(spec) == full
