"""
Time boards and AIs on identical positions:
    python -m bench search -b linked -b bit -a maxn:3 -a "maxn:3:margin(simple)"
    python -m bench playout -b linked -b bit
"""
import sys

from argparse           import ArgumentParser, ArgumentTypeError, Namespace

from nagrica.cli        import AI_HELP, BOARDS, add_game_args, game_settings, parse_ai, positive_int, non_negative_int, full_ai_spec

from .bench             import Variant, format_results, playout_workload, run_variant, search_workload, variants



def _ai(value: str) -> tuple[str, str]:
    spec = value.strip().lower()

    parse_ai(spec)  # Fail early on a bad spec

    return full_ai_spec(spec), spec


def _board(value: str) -> str:
    if value not in BOARDS:
        raise ArgumentTypeError(f"unknown board '{value}' (choose from: {', '.join(BOARDS)})")

    return value



def parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(prog="bench", description="Time board implementations and AIs on identical positions.")

    add_game_args(parser)

    # Boards are compared here, so `--board` from the shared args is replaced by a repeatable `-b`
    parser.set_defaults(board=None)

    parser.add_argument("workload", choices=("search", "playout"), help="search: select moves from random positions. playout: replay and undo random games, no AI")
    parser.add_argument("-b", "--boards", action="append", type=_board, metavar="BOARD", help=f"board to time. Repeat to compare ({', '.join(BOARDS)}; default: all)")
    parser.add_argument("-a", "--ai",     action="append", dest="ais", type=_ai, metavar="TYPE[:OPTION...]", help=f"AI to time (search only). Repeat to compare. {AI_HELP} (default: maxn)")
    parser.add_argument("-r", "--repeat", type=positive_int,     default=5, help="timed runs per variant (default: %(default)s)")
    parser.add_argument("-w", "--warmup", type=non_negative_int, default=1, help="untimed runs before them (default: %(default)s)")
    parser.add_argument("-o", "--opening",   type=non_negative_int, default=4,  help="search: random moves before each position (default: %(default)s)")
    parser.add_argument("-p", "--positions", type=positive_int,     default=3,  help="search: positions per run (default: %(default)s)")
    parser.add_argument("-g", "--games",     type=positive_int,     default=50, help="playout: games per run (default: %(default)s)")
    parser.add_argument("--players", type=positive_int, default=2, help="players per game (default: %(default)s)")
    parser.add_argument("--seed", type=int, default=0, help="seed for positions and games (default: %(default)s)")
    parser.add_argument("-q", "--quiet", action="store_true", help="don't show progress")

    args = parser.parse_args(argv)

    args.boards = args.boards or list(BOARDS)

    if args.workload == "search":
        args.ais = args.ais or [_ai("maxn")]
    elif args.ais:
        parser.error("playout uses no AI, drop -a")

    return args



def main(argv: list[str] | None = None) -> None:
    args        = parse_args(argv)
    settings    = game_settings(args)
    boards      = {name: BOARDS[name] for name in args.boards}
    first       = next(iter(boards.values()))   # Positions are made on this board, then replayed on the rest
    common      = dict(height=args.height, width=args.width, num_players=args.players, seed=args.seed, settings=settings, board_class=first)

    if args.workload == "search":
        workload    = search_workload(opening=args.opening, positions=args.positions, **common)
        searches    = {full: parse_ai(spec) for full, spec in args.ais}
        detail      = f"{args.positions} positions after {args.opening} random moves"
    else:
        workload    = playout_workload(games=args.games, **common)
        searches    = {"": None}
        detail      = f"{args.games} random games"

    print(f"{args.workload}: {detail}, {args.height}x{args.width}, {args.players} players, {args.repeat} runs (+{args.warmup} warmup), seed {args.seed}")
    print()

    timings = []
    options = variants(boards, searches)

    for index, variant in enumerate(options, 1):
        if not args.quiet:
            print(f"\r[{index}/{len(options)}] {variant.name}".ljust(60), end="", file=sys.stderr, flush=True)

        timings.append(run_variant(variant, workload, repeat=args.repeat, warmup=args.warmup))

    if not args.quiet:
        print(file=sys.stderr)

    print(format_results(timings))


if __name__ == "__main__":
    main()
