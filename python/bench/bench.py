from collections.abc    import Callable, Sequence
from dataclasses        import dataclass
from itertools          import product
from random             import Random
from statistics         import median
from time               import perf_counter

from arena              import random_opening
from nagrica.cli        import SearchFactory
from nagrica.game       import BasicGameState
from nagrica.grid       import Board, Edge
from nagrica.settings   import GameSettings


@dataclass(frozen=True)
class Variant:
    name:           str
    board_class:    type[Board]
    search:         SearchFactory | None    = None      # None for workloads that need no search


@dataclass(frozen=True)
class Timing:
    variant:    str
    runs:       tuple[float, ...]       # Seconds per run

    @property
    def best(self) -> float:
        return min(self.runs)

    @property
    def median(self) -> float:
        return median(self.runs)


# Times a single run of a variant. Everything not being measured is set up before the returned callable
Workload = Callable[[Variant], Callable[[], object]]



def _state(variant: Variant, height: int, width: int, num_players: int, settings: GameSettings) -> BasicGameState:
    return BasicGameState(height, width, num_players, board_class=variant.board_class, settings=settings)


def _replay(state: BasicGameState, moves: Sequence[Edge]) -> None:
    for move in moves:
        state.apply(move)



def record_playout(height: int, width: int, num_players: int, *, seed: int, settings: GameSettings, board_class: type[Board]) -> tuple[Edge, ...]:
    """
    A full game of random moves. Edges are the same on every board, so the game can be replayed on any of them
    """
    rng     = Random(seed)
    state   = BasicGameState(height, width, num_players, board_class=board_class, settings=settings)
    moves   = []

    while not state.finished:
        move = rng.choice(state.legal_moves())

        state.apply(move)
        moves.append(move)

    return tuple(moves)



def search_workload(
    *,
    height:         int,
    width:          int,
    num_players:    int,
    opening:        int,
    positions:      int,
    seed:           int,
    settings:       GameSettings,
    board_class:    type[Board],
) -> Workload:
    """
    Select a move from each of `positions` random positions. Every variant gets the same positions
    """
    openings = [
        random_opening(height, width, num_players, moves=opening, rng=Random(f"bench-{seed}-{index}"), settings=settings, board_class=board_class)
        for index in range(positions)
    ]

    def prepare(variant: Variant) -> Callable[[], object]:
        assert variant.search is not None, "the search workload needs an AI"

        states = []

        for moves in openings:
            state = _state(variant, height, width, num_players, settings)

            _replay(state, moves)
            states.append(state)

        def run() -> None:
            search = variant.search(seed)   # type: ignore[misc]  # Fresh per run, so no state carries over

            for state in states:
                search.select_move(state.copy())

        return run

    return prepare


def playout_workload(
    *,
    height:         int,
    width:          int,
    num_players:    int,
    games:          int,
    seed:           int,
    settings:       GameSettings,
    board_class:    type[Board],
) -> Workload:
    """
    Raw board and game state speed: replay `games` full random games, then undo them all. No search involved
    """
    playouts = [
        record_playout(height, width, num_players, seed=seed + index, settings=settings, board_class=board_class)
        for index in range(games)
    ]

    def prepare(variant: Variant) -> Callable[[], object]:
        def run() -> None:
            for moves in playouts:
                state = _state(variant, height, width, num_players, settings)

                _replay(state, moves)

                while state.history:
                    state.undo()

        return run

    return prepare



def variants(boards: dict[str, type[Board]], searches: dict[str, SearchFactory | None]) -> list[Variant]:
    """Every board with every search"""
    return [
        Variant(f"{search_name}/{board_name}" if search else board_name, board, search)
        for (board_name, board), (search_name, search) in product(boards.items(), searches.items())
    ]


def run_variant(variant: Variant, workload: Workload, *, repeat: int, warmup: int = 1) -> Timing:
    """Time `repeat` runs, after `warmup` runs that are thrown away"""
    run = workload(variant)

    for _ in range(warmup):
        run()

    runs = []

    for _ in range(repeat):
        start = perf_counter()

        run()

        runs.append(perf_counter() - start)

    return Timing(variant.name, tuple(runs))



def format_results(timings: Sequence[Timing]) -> str:
    """Fastest first. `vs best` is how many times slower than the fastest, by best run"""
    ranked  = sorted(timings, key=lambda t: t.best)
    width   = max([len(t.variant) for t in ranked] + [len("Variant")])
    header  = f"{'Variant':<{width}}  {'best ms':>10}  {'median ms':>10}  {'max ms':>10}  {'vs best':>8}"
    lines   = [header, "-" * len(header)]

    for t in ranked:
        lines.append(
            f"{t.variant:<{width}}  {t.best * 1000:>10.2f}  {t.median * 1000:>10.2f}  {max(t.runs) * 1000:>10.2f}  {t.best / ranked[0].best:>7.2f}x"
        )

    return "\n".join(lines)
