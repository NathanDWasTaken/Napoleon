"""
Benchmark AIs against each other: python -m arena -c random -c maxn:2 -c "maxn:3:margin(score)"
"""
import sys

from argparse           import ArgumentParser, Namespace
from time               import perf_counter

from nagrica.cli        import AI_HELP, add_game_args, game_settings, non_negative_int, parse_ai, positive_int, split_name

from .arena             import Contestant, GameResult, format_matchups, format_standings, matchups, run_arena, standings



def _contestant(value: str) -> Contestant:
    """
    Parse an AI spec with an optional name, e.g. `maxn:3` or `maxn:3:margin(score)=deep`. Without a name, the spec is the name
    """
    spec, name = split_name(value)

    return Contestant(name or spec, parse_ai(spec))


def _unique_names(contestants: list[Contestant]) -> list[Contestant]:
    """The same name twice (e.g. random vs random) gets numbered: random, random#2"""
    seen:   dict[str, int]      = {}
    unique: list[Contestant]    = []

    for contestant in contestants:
        count                   = seen.get(contestant.name, 0) + 1
        seen[contestant.name]   = count
        name                    = contestant.name if count == 1 else f"{contestant.name}#{count}"

        unique.append(Contestant(name, contestant.search))

    return unique



def parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(
        prog        = "arena",
        description = "Benchmark AIs against each other, on points and on time per move.",
    )

    add_game_args(parser)

    parser.add_argument(
        "-c", "--contestant",
        dest    = "contestants",
        action  = "append",
        type    = _contestant,
        metavar = "TYPE[:OPTION...][=NAME]",
        help    = f"add a contestant. Repeat for each contestant. {AI_HELP} (default: random and maxn)",
    )
    parser.add_argument(
        "-r", "--rounds",
        type    = positive_int,
        default = 10,
        help    = "rounds per group of contestants. Each round plays every seat rotation once (default: %(default)s)",
    )
    parser.add_argument(
        "-n", "--players-per-game",
        type    = positive_int,
        default = 2,
        help    = "players per game. Every group of this size plays (default: %(default)s)",
    )
    parser.add_argument(
        "-o", "--opening",
        type    = non_negative_int,
        default = 3,
        help    = "random moves played at the start of each game, so deterministic AIs don't replay the same game. "
                  "Only moves that capture nothing and leave nothing to capture. "
                  "Each round gets its own opening, shared by all its games (default: %(default)s)",
    )
    parser.add_argument("--seed", type=int, default=0, help="seed for openings and random contestants (default: %(default)s)")
    parser.add_argument("-q", "--quiet", action="store_true", help="don't show progress")

    args = parser.parse_args(argv)

    if args.contestants is None:
        args.contestants = [_contestant("random"), _contestant("maxn")]

    args.contestants = _unique_names(args.contestants)

    if args.players_per_game < 2:
        parser.error("at least 2 players per game are needed")

    if len(args.contestants) < args.players_per_game:
        parser.error(f"at least {args.players_per_game} contestants are needed for {args.players_per_game} players per game")

    return args



def _progress(result: GameResult, done: int, total: int) -> None:
    end = "\n" if done == total else ""

    print(f"\rGame {done}/{total}", end=end, file=sys.stderr, flush=True)



def main(argv: list[str] | None = None) -> None:
    args    = parse_args(argv)
    start   = perf_counter()

    results = run_arena(
        args.contestants,
        rounds              = args.rounds,
        height              = args.height,
        width               = args.width,
        players_per_game    = args.players_per_game,
        settings            = game_settings(args),
        opening_moves       = args.opening,
        seed                = args.seed,
        on_result           = None if args.quiet else _progress,
    )

    print(f"{len(results)} games on {args.height}x{args.width} in {perf_counter() - start:.1f}s")
    print()
    print(format_standings(standings(results)))
    print()
    print(format_matchups(matchups(results)))


if __name__ == "__main__":
    main()
