from argparse           import ArgumentParser, ArgumentTypeError, Namespace

from nagrica.cli        import AI_HELP, AI_TYPES, add_game_args, game_settings, parse_ai, split_name
from nagrica.game       import Player
from nagrica.game.match import Match
from nagrica.players    import ComputerPlayer, HumanPlayer
from nagrica.ui         import render_board


DEFAULT_PLAYERS = [("human", None), ("human", None)]



def _player_spec(value: str) -> tuple[str, str | None]:
    """
    Parse `human` or an AI spec, with an optional name: e.g. `human=Alice` or `maxn:3=Bob`
    """
    spec, name = split_name(value)

    if spec.split(":")[0] == "human":
        if spec != "human":
            raise ArgumentTypeError("human takes no options (name a player with TYPE=NAME, e.g. human=Alice)")
    else:
        parse_ai(spec)  # Validate now, so mistakes show as usage errors

    return spec, name



def parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(
        prog        = "nagrica",
        description = "Play Napoleon Grid Capture.",
    )

    add_game_args(parser)

    parser.add_argument(
        "-p", "--player",
        dest    = "players",
        action  = "append",
        type    = _player_spec,
        metavar = "TYPE[:OPTION...][=NAME]",
        help    = f"add a player, in turn order. Repeat for each player. "
                  f"Types: human, {', '.join(AI_TYPES)}. {AI_HELP} (default: two human players)",
    )

    args = parser.parse_args(argv)

    if args.players is None:
        args.players = DEFAULT_PLAYERS

    if len(args.players) < 2:
        parser.error("at least 2 players are needed")

    return args



def build_players(specs: list[tuple[str, str | None]]) -> list[Player]:
    """
    Each computer player gets its own search instance,
    so two computers never share state (e.g. a random number generator).
    """
    players: list[Player] = []

    for seat, (spec, name) in enumerate(specs):
        name = name or f"Player {seat + 1}"

        if spec == "human":
            players.append(HumanPlayer(name, seat))
        else:
            players.append(ComputerPlayer(name, seat, search_algo=parse_ai(spec)(None)))

    return players


def print_results(match: Match) -> None:
    scores  = match.state.scores
    best    = max(scores)
    winners = [player.name for player in match.players if scores[player.seat] == best]

    print(render_board(match.state.board, axes=True))
    print()

    for player in match.players:
        print(f"{player.name}: {scores[player.seat]}")

    print()
    print(f"Winner: {winners[0]}" if len(winners) == 1 else f"Draw between: {', '.join(winners)}")



def main(argv: list[str] | None = None) -> None:
    args    = parse_args(argv)
    players = build_players(args.players)
    match   = Match(players, height=args.height, width=args.width, settings=game_settings(args))

    try:
        match.start()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C, or the end of piped input
        print("\nGame aborted.")
        return

    print_results(match)


if __name__ == "__main__":
    main()
