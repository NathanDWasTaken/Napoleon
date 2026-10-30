"""
Command line parts shared by `python -m nagrica` and the arena.

AIs are written as `TYPE[:OPTION...]`, e.g. `random`, `maxn:3` or `maxn:3:margin(simple)`.
Quote specs with parentheses in the shell: -p "maxn:3:margin(simple)"
"""
from argparse           import ArgumentParser, ArgumentTypeError, Namespace
from collections.abc    import Callable

from nagrica.ai         import CurrentScore, EvaluationAlgorithm, Max_N, RandomMove, SearchAlgorithm, SimpleEval
from nagrica.ai.eval    import MarginEval
from nagrica.settings   import GameSettings, LastCellResolution


# Builds a fresh search from a seed (for searches with randomness). None means unseeded
SearchFactory = Callable[[int | None], SearchAlgorithm]



# ---------------------------------------------------------------- numbers


def positive_int(value: str) -> int:
    number = _int(value)

    if number < 1:
        raise ArgumentTypeError(f"must be at least 1, got {value}")

    return number


def non_negative_int(value: str) -> int:
    number = _int(value)

    if number < 0:
        raise ArgumentTypeError(f"must be at least 0, got {value}")

    return number


def _int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise ArgumentTypeError(f"not a number: '{value}'")



# ---------------------------------------------------------------- game


LAST_CELL = {
    "current":  LastCellResolution.CURRENT_PLAYER,
    "next":     LastCellResolution.NEXT_PLAYER,
}


def add_game_args(parser: ArgumentParser) -> None:
    """Board size and game settings"""
    parser.add_argument("--height", type=positive_int, default=4, help="board height (default: %(default)s)")
    parser.add_argument("--width",  type=positive_int, default=4, help="board width (default: %(default)s)")
    parser.add_argument(
        "--last-cell",
        choices = LAST_CELL,
        default = "next",
        help    = "who gets the last cell: the current or the next player (default: %(default)s)",
    )


def game_settings(args: Namespace) -> GameSettings:
    return GameSettings(LAST_CELL[args.last_cell])



# ---------------------------------------------------------------- evaluations


# Evaluation algorithms selectable for searches that use one. Register new ones here
EVALUATIONS: dict[str, Callable[[], EvaluationAlgorithm]] = {
    "score":    CurrentScore,
    "simple":   SimpleEval,
}

# Wrappers around an evaluation, written as a call: e.g. `margin(simple)`. Register new ones here
EVAL_MODIFIERS: dict[str, Callable[[EvaluationAlgorithm], EvaluationAlgorithm]] = {
    "margin":   MarginEval,
}


def parse_evaluation(spec: str) -> Callable[[], EvaluationAlgorithm]:
    """
    Parse `EVAL` or `MODIFIER(EVAL)`, which nests: e.g. `score`, `margin(simple)`
    """
    name, bracket, rest = spec.partition("(")

    if not bracket:
        if name in EVAL_MODIFIERS:
            raise ArgumentTypeError(f"'{name}' wraps an evaluation, e.g. {name}(score)")

        if name not in EVALUATIONS:
            raise ArgumentTypeError(f"unknown evaluation '{name}' (choose from: {', '.join(EVALUATIONS)})")

        return EVALUATIONS[name]

    if not rest.endswith(")"):
        raise ArgumentTypeError(f"missing ')' in evaluation '{spec}'")

    if name not in EVAL_MODIFIERS:
        raise ArgumentTypeError(f"unknown evaluation modifier '{name}' (choose from: {', '.join(EVAL_MODIFIERS)})")

    modifier    = EVAL_MODIFIERS[name]
    inner       = parse_evaluation(rest[:-1])

    return lambda: modifier(inner())



# ---------------------------------------------------------------- AIs


DEFAULT_MAX_DEPTH = 3


def _random(options: list[str]) -> SearchFactory:
    if options:
        raise ArgumentTypeError("random takes no options")

    return lambda seed: RandomMove(seed=seed)


def _maxn(options: list[str]) -> SearchFactory:
    """maxn[:DEPTH[:EVAL]]"""
    if len(options) > 2:
        raise ArgumentTypeError("maxn takes at most a depth and an evaluation: maxn[:DEPTH[:EVAL]]")

    depth       = positive_int(options[0]) if options else DEFAULT_MAX_DEPTH
    evaluation  = parse_evaluation(options[1] if len(options) > 1 else "score")

    return lambda seed: Max_N(evaluation(), max_depth=depth)


# AI types selectable from the CLI, built from the options after the type. Register new AIs here
AI_TYPES: dict[str, Callable[[list[str]], SearchFactory]] = {
    "random":   _random,
    "maxn":     _maxn,
}

AI_HELP = (
    f"AIs: random, maxn[:DEPTH[:EVAL]] with EVAL one of {', '.join(EVALUATIONS)}, "
    f"optionally wrapped in {', '.join(f'{m}(...)' for m in EVAL_MODIFIERS)}. "
    f"E.g. \"maxn:3:margin(simple)\" (quote the brackets in the shell)"
)


def parse_ai(spec: str) -> SearchFactory:
    """
    Parse `TYPE[:OPTION...]`, e.g. `random` or `maxn:3:margin(score)`
    """
    kind, *options = spec.split(":")

    if kind not in AI_TYPES:
        raise ArgumentTypeError(f"unknown AI type '{kind}' (choose from: {', '.join(AI_TYPES)})")

    return AI_TYPES[kind](options)


def split_name(value: str) -> tuple[str, str | None]:
    """
    Split `SPEC[=NAME]` into the spec (lower case) and the name, if any: e.g. `maxn:3=Bob`
    """
    spec, _, name = value.partition("=")

    return spec.strip().lower(), name.strip() or None
