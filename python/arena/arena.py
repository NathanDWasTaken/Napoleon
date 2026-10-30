from collections.abc    import Callable, Iterator, Sequence
from dataclasses        import dataclass, field, replace
from itertools          import combinations
from random             import Random
from statistics         import mean
from time               import perf_counter

from nagrica.ai         import SearchAlgorithm
from nagrica.capture    import CaptureEvaluation, GreedyDFS
from nagrica.game       import GameState, Match, Move
from nagrica.grid       import Board
from nagrica.grid.boards import LinkedBoard
from nagrica.players    import ComputerPlayer
from nagrica.settings   import GameSettings


# Builds a fresh search for a single game, from a seed (for searches with randomness)
SearchFactory = Callable[[int], SearchAlgorithm]



@dataclass(frozen=True)
class Contestant:
    name:   str
    search: SearchFactory



class TimedPlayer(ComputerPlayer):
    """
    Computer player that records how long each move takes to select
    """
    move_times: list[float]


    def __init__(self, name: str, seat: int, *, search_algo: SearchAlgorithm) -> None:
        self.move_times = []

        super().__init__(name, seat, search_algo=search_algo)


    def make_move(self, gameState: GameState) -> Move:
        start   = perf_counter()
        move    = super().make_move(gameState)

        self.move_times.append(perf_counter() - start)

        return move



@dataclass(frozen=True)
class GameResult:
    group:      tuple[str, ...]                 # Contestants in the game, in the order they were given to the arena
    lineup:     tuple[str, ...]                 # Contestants by seat
    scores:     tuple[int, ...]                 # By seat
    move_times: tuple[tuple[float, ...], ...]   # Seconds per move, by seat
    opening:    tuple[Move, ...]        = ()    # Random moves played before the contestants took over


    @property
    def winners(self) -> tuple[str, ...]:
        best = max(self.scores)

        return tuple(name for name, score in zip(self.lineup, self.scores) if score == best)


    def score_of(self, name: str) -> int:
        return self.scores[self.lineup.index(name)]



@dataclass
class Standing:
    name:           str
    games:          int         = 0
    wins:           int         = 0
    draws:          int         = 0
    losses:         int         = 0
    points:         int         = 0
    points_total:   int         = 0     # Points handed out in all games of this contestant
    move_times:     list[float] = field(default_factory=list)


    @property
    def score_rate(self) -> float:
        """Wins count 1, draws 1/2"""
        return (self.wins + self.draws / 2) / self.games if self.games else 0.0

    @property
    def avg_points(self) -> float:
        return self.points / self.games if self.games else 0.0

    @property
    def point_share(self) -> float:
        return self.points / self.points_total if self.points_total else 0.0

    @property
    def mean_move_time(self) -> float:
        return mean(self.move_times) if self.move_times else 0.0

    @property
    def max_move_time(self) -> float:
        return max(self.move_times, default=0.0)



def schedule(contestants: Sequence[Contestant], rounds: int, players_per_game: int) -> Iterator[tuple[int, tuple[Contestant, ...]]]:
    """
    Every group of `players_per_game` contestants plays `rounds` rounds. Yields (round, lineup).
    Each round rotates the group through the seats, so nobody profits from always moving first.
    """
    for group in combinations(contestants, players_per_game):
        for round_ in range(rounds):
            for rotation in range(players_per_game):
                yield round_, group[rotation:] + group[:rotation]



def _captures(state: GameState, move: Move) -> bool:
    """Whether `move` captures anything (including the last cell going to the next player)"""
    turns = len(state.history)

    state.apply(move)
    captured = any(turn.capture.points for turn in state.history[turns:])
    state.undo()

    return captured


def is_safe(state: GameState, move: Move) -> bool:
    """
    A move that captures nothing, and leaves the next player nothing to capture
    """
    if _captures(state, move):
        return False

    state.apply(move)
    safe = not any(_captures(state, reply) for reply in state.legal_moves())
    state.undo()

    return safe


def random_opening(
    height:         int,
    width:          int,
    num_players:    int,
    *,
    moves:          int,
    rng:            Random,
    settings:       GameSettings                = GameSettings(),
    capture_eval:   type[CaptureEvaluation]     = GreedyDFS,
    board_class:    type[Board]                 = LinkedBoard,
) -> tuple[Move, ...]:
    """
    Up to `moves` random safe moves, so games between deterministic AIs differ.
    Stops early when no safe move is left, rather than handing out cells.
    """
    state   = GameState(height, width, num_players, capture_eval=capture_eval, board_class=board_class, settings=settings)
    opening = []

    for _ in range(moves):
        safe = [move for move in state.legal_moves() if is_safe(state, move)]

        if not safe:
            break

        move = rng.choice(safe)

        state.apply(move)
        opening.append(move)

    return tuple(opening)



def play_game(
    lineup:         Sequence[Contestant],
    *,
    height:         int,
    width:          int,
    settings:       GameSettings    = GameSettings(),
    opening:        Sequence[Move]  = (),
    seed:           int             = 0,
) -> GameResult:
    """
    Play a single game. The `opening` moves are played first, in turn order, without the contestants
    """
    rng     = Random(seed)
    players = [
        TimedPlayer(contestant.name, seat, search_algo=contestant.search(rng.randrange(2 ** 32)))
        for seat, contestant in enumerate(lineup)
    ]
    match   = Match(players, height, width, settings=settings)

    for move in opening:
        match.state.apply(move)

    match.start()

    return GameResult(
        group       = tuple(contestant.name for contestant in lineup),
        lineup      = tuple(player.name for player in players),
        scores      = tuple(match.state.scores),
        move_times  = tuple(tuple(player.move_times) for player in players),
        opening     = tuple(opening),
    )


def run_arena(
    contestants:        Sequence[Contestant],
    *,
    rounds:             int,
    height:             int,
    width:              int,
    players_per_game:   int                                 = 2,
    settings:           GameSettings                        = GameSettings(),
    opening_moves:      int                                 = 3,
    seed:               int                                 = 0,
    on_result:          Callable[[GameResult, int, int], None] | None = None,
) -> list[GameResult]:
    """
    Play every scheduled game. `on_result(result, done, total)` is called after each game, e.g. for progress.

    Each round starts from its own random opening of `opening_moves` safe moves. Every seat rotation
    (and every group) in a round gets the same opening, so contestants are compared on the same positions.
    """
    names = [contestant.name for contestant in contestants]

    if len(set(names)) != len(names):
        raise ValueError(f"contestant names must be unique, got {names}")

    if not 2 <= players_per_game <= len(contestants):
        raise ValueError(f"need at least {max(players_per_game, 2)} contestants for {players_per_game} players per game")

    lineups     = list(schedule(contestants, rounds, players_per_game))
    openings    = [
        random_opening(height, width, players_per_game, moves=opening_moves, rng=Random(f"opening-{seed}-{round_}"), settings=settings)
        for round_ in range(rounds)
    ]
    results     = []

    for index, (round_, lineup) in enumerate(lineups):
        result = play_game(lineup, height=height, width=width, settings=settings, opening=openings[round_], seed=seed + index)

        # Group in the order the contestants were given, so results of the same group can be combined
        result = replace(result, group=tuple(name for name in names if name in result.lineup))
        results.append(result)

        if on_result:
            on_result(result, index + 1, len(lineups))

    return results



def standings(results: Sequence[GameResult]) -> list[Standing]:
    """Per contestant totals, best first"""
    table: dict[str, Standing] = {}

    for result in results:
        winners = result.winners
        total   = sum(result.scores)

        for name, score, times in zip(result.lineup, result.scores, result.move_times):
            standing = table.setdefault(name, Standing(name))

            standing.games          += 1
            standing.points         += score
            standing.points_total   += total
            standing.move_times.extend(times)

            if name not in winners:
                standing.losses += 1
            elif len(winners) == 1:
                standing.wins   += 1
            else:
                standing.draws  += 1

    return sorted(table.values(), key=lambda s: (s.score_rate, s.point_share), reverse=True)


def matchups(results: Sequence[GameResult]) -> dict[tuple[str, ...], list[Standing]]:
    """Standings per group of contestants that played each other"""
    groups: dict[tuple[str, ...], list[GameResult]] = {}

    for result in results:
        groups.setdefault(result.group, []).append(result)

    return {
        group: sorted(standings(group_results), key=lambda s: group.index(s.name))
        for group, group_results in groups.items()
    }



def format_standings(table: Sequence[Standing]) -> str:
    width   = max([len(s.name) for s in table] + [len("Contestant")])
    header  = f"{'Contestant':<{width}}  {'Games':>5}  {'W':>4}  {'D':>4}  {'L':>4}  {'Score':>6}  {'Avg pts':>7}  {'Pts %':>6}  {'ms/move':>8}  {'max ms':>8}"
    lines   = [header, "-" * len(header)]

    for s in table:
        lines.append(
            f"{s.name:<{width}}  {s.games:>5}  {s.wins:>4}  {s.draws:>4}  {s.losses:>4}  "
            f"{s.score_rate:>6.1%}  {s.avg_points:>7.2f}  {s.point_share:>6.1%}  "
            f"{s.mean_move_time * 1000:>8.2f}  {s.max_move_time * 1000:>8.2f}"
        )

    return "\n".join(lines)


def format_matchups(groups: dict[tuple[str, ...], list[Standing]]) -> str:
    lines = []

    for group, table in groups.items():
        record  = " - ".join(f"{s.wins}" for s in table)
        points  = " - ".join(f"{s.avg_points:.2f}" for s in table)
        draws   = table[0].draws

        lines.append(f"{' vs '.join(group)}:  wins {record}  (draws {draws}),  avg pts {points}")

    return "\n".join(lines)
