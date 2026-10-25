from argparse           import ArgumentParser, ArgumentTypeError, Namespace

from nagrica.game       import Player
from nagrica.game.match import Match
from nagrica.players    import HumanPlayer, RandomPlayer
from nagrica.ui         import render_board


# Player types selectable from the CLI. Register new (AI) players here
PLAYER_TYPES: dict[str, type[Player]] = {
    "human":    HumanPlayer,
    "random":   RandomPlayer
}

DEFAULT_PLAYERS = [("human", None), ("human", None)]



def _positive_int(value: str) -> int:
    number = int(value)

    if number < 1:
        raise ArgumentTypeError(f"must be at least 1, got {value}")

    return number


def _player_spec(value: str) -> tuple[str, str | None]:
    """
    Parse `TYPE` or `TYPE:NAME`, e.g. `human` or `human:Alice`
    """
    kind, _, name   = value.partition(":")
    kind            = kind.lower()

    if kind not in PLAYER_TYPES:
        raise ArgumentTypeError(f"unknown player type '{kind}' (choose from: {', '.join(PLAYER_TYPES)})")

    return kind, name or None



def parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(
        prog        = "nagrica",
        description = "Play Napoleon Grid Capture.",
    )

    parser.add_argument(
        "--height",
        type    = _positive_int,
        default = 4,
        help    = "board height (default: %(default)s)",
    )
    parser.add_argument(
        "--width",
        type    = _positive_int,
        default = 4,
        help    = "board width (default: %(default)s)",
    )
    parser.add_argument(
        "-p", "--player",
        dest    = "players",
        action  = "append",
        type    = _player_spec,
        metavar = "TYPE[:NAME]",
        help    = f"add a player, in turn order. Repeat for each player. "
                  f"Types: {', '.join(PLAYER_TYPES)} (default: two human players)",
    )

    args = parser.parse_args(argv)

    if args.players is None:
        args.players = DEFAULT_PLAYERS

    if len(args.players) < 2:
        parser.error("at least 2 players are needed")

    return args



def build_players(specs: list[tuple[str, str | None]]) -> list[Player]:
    return [
        PLAYER_TYPES[kind](name or f"Player {seat + 1}", seat)
        for seat, (kind, name) in enumerate(specs)
    ]


def print_results(match: Match) -> None:
    scores  = match.state.scores
    best    = max(scores)
    winners = [player.name for player in match.players if scores[player.seat] == best]

    print(render_board(match.state.board))
    print()

    for player in match.players:
        print(f"{player.name}: {scores[player.seat]}")

    print()
    print(f"Winner: {winners[0]}" if len(winners) == 1 else f"Draw between: {', '.join(winners)}")



def main(argv: list[str] | None = None) -> None:
    args    = parse_args(argv)
    players = build_players(args.players)
    match   = Match(players, height=args.height, width=args.width)

    try:
        match.start()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C, or the end of piped input
        print("\nGame aborted.")
        return

    print_results(match)


if __name__ == "__main__":
    main()
