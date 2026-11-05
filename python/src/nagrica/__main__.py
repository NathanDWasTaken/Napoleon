import sys

from argparse           import ArgumentParser, ArgumentTypeError, Namespace
from datetime           import date
from pathlib            import Path

from nagrica.cli        import AI_HELP, AI_TYPES, LAST_CELL, add_game_args, board_class, full_ai_spec, game_settings, parse_ai, split_name
from nagrica.game       import CompleteGameState, IllegalMove, Player
from nagrica.game.match import Match
from nagrica.players    import ComputerPlayer, HumanPlayer
from nagrica.settings   import GameSettings
from nagrica.ui         import NotationError, Record, format_move, format_record, parse_record, render_board


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
    parser.add_argument(
        "--record",
        type    = Path,
        metavar = "FILE",
        help    = "save the moves of the game to FILE, also when the game is aborted",
    )
    parser.add_argument(
        "--overwrite",
        action  = "store_true",
        help    = "allow --record to replace a file that already exists",
    )
    parser.add_argument(
        "--replay",
        type    = Path,
        metavar = "FILE",
        help    = "replay a recorded game move by move instead of playing. "
                  "The board size, last cell rule and players come from the record",
    )

    args = parser.parse_args(argv)

    if args.players is None:
        args.players = DEFAULT_PLAYERS

    if len(args.players) < 2:
        parser.error("at least 2 players are needed")

    # Fail before playing, rather than after a whole game
    if args.record and args.record.exists() and not args.overwrite:
        parser.error(f"{args.record} already exists, pass --overwrite to replace it")

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
    print(render_board(match.state.board, axes=True, owners=match.state.captured))
    print()
    _print_scores(match.state, [player.name for player in match.players])


def _print_scores(state: CompleteGameState, names: list[str]) -> None:
    scores  = state.scores
    best    = max(scores)
    winners = [name for name, score in zip(names, scores) if score == best]

    for name, score in zip(names, scores):
        print(f"{name}: {score}")

    print()
    print(f"Winner: {winners[0]}" if len(winners) == 1 else f"Draw between: {', '.join(winners)}")



# ---------------------------------------------------------------- records


def record_of(match: Match, args: Namespace) -> Record:
    """The moves of the match so far. Turns without a wall (the last cell going to the next player) follow from the moves"""
    state = match.state

    return Record(
        height      = args.height,
        width       = args.width,
        last_cell   = args.last_cell,
        players     = [
            (player.name, spec if spec == "human" else full_ai_spec(spec))
            for player, (spec, _) in zip(match.players, args.players)
        ],
        moves       = [turn.wall for turn in state.history if turn.wall is not None],
        result      = "-".join(map(str, state.scores)) if state.finished else "*",
        tags        = {"Date": date.today().strftime("%Y.%m.%d")},
    )


def save_record(match: Match, args: Namespace) -> None:
    args.record.write_text(format_record(record_of(match, args)), encoding="utf-8")
    print(f"Game recorded to {args.record}")


def replay(args: Namespace) -> None:
    """Show a recorded game move by move. Waits for Enter between moves when run in a terminal"""
    try:
        record = parse_record(args.replay.read_text(encoding="utf-8"))
    except (OSError, NotationError) as error:
        sys.exit(f"Can't replay {args.replay}: {error}")

    if record.last_cell not in LAST_CELL:
        sys.exit(f"Can't replay {args.replay}: unknown LastCell '{record.last_cell}', expected one of {', '.join(LAST_CELL)}")

    names   = [name for name, _ in record.players]
    state   = CompleteGameState(
        record.height,
        record.width,
        record.num_players,
        board_class     = board_class(args),
        settings        = GameSettings(LAST_CELL[record.last_cell]),
    )
    pause   = sys.stdin.isatty()

    for seat, (name, type_) in enumerate(record.players, start=1):
        print(f"Seat {seat}: {name} ({type_})")

    print()
    print(render_board(state.board, axes=True, notation=True))

    for index, move in enumerate(record.moves):
        if pause:
            try:
                if input("\n[Enter] next move, [q] quit > ").strip().lower() == "q":
                    return
            except EOFError:
                # No more input (on Windows, NUL also counts as a terminal): show the rest at once
                pause = False

        number  = f"{index // record.num_players + 1}."
        name    = names[state.current_seat]

        try:
            state.apply(move)
        except IllegalMove:
            sys.exit(f"Move {number} {format_move(move)} by {name} is not legal")

        print()
        print(f"{number} {name}: {format_move(move)}")
        print(render_board(state.board, axes=True, notation=True, owners=state.captured))

    print()

    if not state.finished:
        print("The record ends before the game is finished.")
        print()

    _print_scores(state, names)



def main(argv: list[str] | None = None) -> None:
    args    = parse_args(argv)

    if args.replay:
        try:
            replay(args)
        except (KeyboardInterrupt, EOFError):
            print("\nReplay stopped.")
        return

    players = build_players(args.players)
    match   = Match(players, height=args.height, width=args.width, board_class=board_class(args), settings=game_settings(args))

    try:
        match.game_loop()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C, or the end of piped input
        print("\nGame aborted.")

        if args.record:
            save_record(match, args)
        return

    print_results(match)

    if args.record:
        print()
        save_record(match, args)


if __name__ == "__main__":
    main()
