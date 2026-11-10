"""
Pygame front end: `python -m nagrica.ui.gui` or `nagrica-gui`. Needs the `gui` extra (`uv sync --extra gui`).

Players are chosen like in the CLI (`-p human -p maxn:3`). Click next to a wall spot to place it.
Computers think in a background thread, so the window stays responsive.
"""
import sys

from argparse           import ArgumentParser, Namespace
from collections.abc    import Sequence
from threading          import Thread

try:
    import pygame
except ImportError:
    sys.exit("The GUI needs pygame. Install it with: uv sync --extra gui")

from nagrica.__main__   import _player_spec, build_players
from nagrica.cli        import AI_HELP, AI_TYPES, add_game_args, board_class, game_settings
from nagrica.game       import CompleteGameState, Player
from nagrica.grid       import Coord, Direction, Edge
from nagrica.players    import ComputerPlayer


DEFAULT_PLAYERS = [("human", None), ("maxn", None)]

WINDOW_SIZE     = (960, 720)
SIDEBAR_WIDTH   = 260
MARGIN          = 40
SEAT_ROW_WIDTH  = SIDEBAR_WIDTH - 20
MAX_CELL        = 110
FPS             = 60

BACKGROUND      = (24, 26, 33)
PANEL           = (32, 35, 44)
CELL_FREE       = (52, 56, 70)
GUIDE           = (74, 79, 98)
GUIDE_HOVER     = (190, 195, 215)
BORDER          = (210, 213, 224)
TEXT            = (230, 232, 240)
TEXT_DIM        = (140, 146, 165)

# One colour per seat, repeated if there are more players
SEAT_COLORS = [
    (237, 106, 94),
    (86, 168, 245),
    (245, 197, 66),
    (112, 205, 129),
    (186, 134, 235),
    (240, 143, 205),
]

Rect = tuple[int, int, int, int]



def seat_color(seat: int) -> tuple[int, int, int]:
    return SEAT_COLORS[seat % len(SEAT_COLORS)]


def dim(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    """Blend a colour towards the free-cell colour, so captured cells stay readable"""
    return (
        int(CELL_FREE[0] + (color[0] - CELL_FREE[0]) * factor),
        int(CELL_FREE[1] + (color[1] - CELL_FREE[1]) * factor),
        int(CELL_FREE[2] + (color[2] - CELL_FREE[2]) * factor),
    )



# ---------------------------------------------------------------- computer moves


class Thinker:
    """Runs a computer player's `make_move` in a thread and hands the result back when ready"""

    def __init__(self, player: Player, state: CompleteGameState) -> None:
        self.move:  Edge | None         = None
        self.error: BaseException | None = None
        self._thread = Thread(target=self._run, args=(player, state.copy()), daemon=True)
        self._thread.start()


    def _run(self, player: Player, state: CompleteGameState) -> None:
        try:
            self.move = player.make_move(state)
        except BaseException as error:  # Shown in the window instead of killing the thread silently
            self.error = error


    @property
    def done(self) -> bool:
        return self.move is not None or self.error is not None



# ---------------------------------------------------------------- app


class App:

    def __init__(self, args: Namespace) -> None:
        self.args       = args
        self.screen     = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        self.clock      = pygame.time.Clock()
        self.font       = pygame.font.SysFont(None, 28)
        self.small      = pygame.font.SysFont(None, 22)
        self.big        = pygame.font.SysFont(None, 44)

        self.players:   list[Player]
        self.state:     CompleteGameState
        self.thinker:   Thinker | None
        self.message:   str
        self.failed:    bool
        self._legal:   tuple[int, list[Edge]]

        self.new_game()


    def new_game(self) -> None:
        args            = self.args
        self.players    = build_players(args.players)
        self.state      = CompleteGameState(
            args.height,
            args.width,
            len(self.players),
            board_class = board_class(args),
            settings    = game_settings(args),
        )
        self.thinker    = None  # A thinker still running for the old game is ignored and dies with the process
        self.message    = ""
        self.failed     = False
        self._legal     = (-1, [])


    # ---- state helpers

    @property
    def player(self) -> Player:
        return self.players[self.state.current_seat]

    @property
    def human_to_move(self) -> bool:
        return not self.state.finished and not isinstance(self.player, ComputerPlayer)

    def legal_moves(self) -> list[Edge]:
        tick, moves = self._legal

        if tick != self.state.tick:
            moves       = self.state.legal_moves()
            self._legal = (self.state.tick, moves)

        return moves

    def play(self, move: Edge) -> None:
        self.state.apply(move)
        self.message = ""


    # ---- layout

    def layout(self) -> tuple[int, int, int]:
        """Cell size and the top left corner of the board"""
        width, height   = self.screen.get_size()
        area_w          = width - SIDEBAR_WIDTH - 2 * MARGIN
        area_h          = height - 2 * MARGIN
        board           = self.state.board
        cell            = max(10, min(MAX_CELL, area_w // board.width, area_h // board.height))
        left            = MARGIN + (area_w - cell * board.width) // 2
        top             = MARGIN + (area_h - cell * board.height) // 2

        return cell, left, top

    def edge_points(self, edge: Edge, cell: int, left: int, top: int) -> tuple[tuple[int, int], tuple[int, int]]:
        """Screen end points of the wall `edge` (a NORTH or EAST edge). NORTH is up on screen"""
        height  = self.state.board.height
        x, y    = edge.coord

        if edge.direction == Direction.NORTH:
            line_y = top + (height - 1 - y) * cell

            return (left + x * cell, line_y), (left + (x + 1) * cell, line_y)

        line_x = left + (x + 1) * cell

        return (line_x, top + (height - 1 - y) * cell), (line_x, top + (height - y) * cell)

    def edge_at(self, pos: tuple[int, int], cell: int, left: int, top: int) -> Edge | None:
        """The legal wall closest to `pos`, if the mouse is on the board"""
        board   = self.state.board
        mx, my  = pos

        if not (left <= mx < left + cell * board.width and top <= my < top + cell * board.height):
            return None

        best:       Edge | None = None
        best_dist               = float("inf")

        for edge in self.legal_moves():
            (x1, y1), (x2, y2)  = self.edge_points(edge, cell, left, top)
            dist                = (mx - (x1 + x2) / 2) ** 2 + (my - (y1 + y2) / 2) ** 2

            if dist < best_dist:
                best, best_dist = edge, dist

        return best


    # ---- loop

    def run(self) -> None:
        while True:
            for event in pygame.event.get():
                if self.handle(event):
                    return

            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle(self, event: pygame.event.Event) -> bool:
        """Act on one event. Returns True when the window should close"""
        if event.type == pygame.QUIT:
            return True

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                return True

            if event.key == pygame.K_r:
                self.new_game()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.human_to_move:
            edge = self.edge_at(event.pos, *self.layout())

            if edge is not None:
                self.play(edge)

        return False

    def update(self) -> None:
        if self.state.finished:
            return

        if not isinstance(self.player, ComputerPlayer) or self.failed:
            return

        if self.thinker is None:
            self.thinker = Thinker(self.player, self.state)
        elif self.thinker.done:
            thinker, self.thinker = self.thinker, None

            if thinker.error is not None:
                self.failed  = True  # Stay on this turn; press R to start over
                self.message = f"{self.player.name} failed: {thinker.error!r}"
            else:
                assert thinker.move is not None
                self.play(thinker.move)


    # ---- drawing

    def draw(self) -> None:
        cell, left, top = self.layout()
        state           = self.state
        board           = state.board
        hover           = self.edge_at(pygame.mouse.get_pos(), cell, left, top) if self.human_to_move else None

        self.screen.fill(BACKGROUND)

        self.draw_cells(cell, left, top)

        # Open wall spots, as a faint grid
        for edge in self.legal_moves():
            start, end = self.edge_points(edge, cell, left, top)
            pygame.draw.line(self.screen, GUIDE, start, end, 2)

        if hover is not None:
            start, end = self.edge_points(hover, cell, left, top)
            pygame.draw.line(self.screen, GUIDE_HOVER, start, end, 6)

        wall = max(4, cell // 12)

        for edge, seat in state.placed.items():
            start, end = self.edge_points(edge, cell, left, top)
            pygame.draw.line(self.screen, seat_color(seat), start, end, wall)

        # Mark the latest wall
        last = next((turn.wall for turn in reversed(state.history) if turn.wall is not None), None)

        if last is not None:
            start, end = self.edge_points(last, cell, left, top)
            pygame.draw.line(self.screen, TEXT, start, end, max(2, wall // 2))

        # Board border and corner dots
        pygame.draw.rect(self.screen, BORDER, (left, top, cell * board.width, cell * board.height), 3)

        for x in range(board.width + 1):
            for y in range(board.height + 1):
                pygame.draw.circle(self.screen, BORDER, (left + x * cell, top + y * cell), 3)

        self.draw_axes(cell, left, top)
        self.draw_sidebar()

        pygame.display.flip()

    def draw_cells(self, cell: int, left: int, top: int) -> None:
        state   = self.state
        height  = state.board.height
        inset   = 2

        for x in range(state.board.width):
            for y in range(height):
                owner   = state.captured.get(Coord(x, y))
                color   = CELL_FREE if owner is None else dim(seat_color(owner), 0.55)
                rect    = (left + x * cell + inset, top + (height - 1 - y) * cell + inset, cell - 2 * inset, cell - 2 * inset)

                pygame.draw.rect(self.screen, color, rect)

                if owner is not None:
                    label = self.font.render(str(owner + 1), True, seat_color(owner))
                    self.screen.blit(label, label.get_rect(center=(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2)))

    def draw_axes(self, cell: int, left: int, top: int) -> None:
        board = self.state.board

        for x in range(board.width):
            label = self.small.render(str(x), True, TEXT_DIM)
            self.screen.blit(label, label.get_rect(center=(left + x * cell + cell // 2, top + board.height * cell + 16)))

        for y in range(board.height):
            label = self.small.render(str(y), True, TEXT_DIM)
            self.screen.blit(label, label.get_rect(center=(left - 16, top + (board.height - 1 - y) * cell + cell // 2)))

    def draw_sidebar(self) -> None:
        width, height   = self.screen.get_size()
        panel           = pygame.Rect(width - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, height)
        state           = self.state
        scores          = state.scores
        x               = panel.left + 24
        y               = 28

        pygame.draw.rect(self.screen, PANEL, panel)

        self.text(self.big, "Napoleon", TEXT, (x, y))
        y += 64

        for seat, player in enumerate(self.players):
            active = not state.finished and seat == state.current_seat

            if active:
                pygame.draw.rect(self.screen, BACKGROUND, (panel.left + 10, y - 8, SEAT_ROW_WIDTH, 52), border_radius=8)

            pygame.draw.circle(self.screen, seat_color(seat), (x + 8, y + 16), 8)
            self.text(self.font, player.name, TEXT, (x + 28, y))
            self.text(self.small, "computer" if isinstance(player, ComputerPlayer) else "human", TEXT_DIM, (x + 28, y + 24))
            self.text(self.big, str(scores[seat]), seat_color(seat), (panel.right - 70, y + 2))

            y += 64

        y += 12

        if state.finished:
            best    = max(scores)
            winners = [player.name for player, score in zip(self.players, scores) if score == best]
            status  = f"{winners[0]} wins!" if len(winners) == 1 else "Draw"
        elif isinstance(self.player, ComputerPlayer):
            status  = f"{self.player.name} is thinking..."
        else:
            status  = f"{self.player.name}: place a wall"

        self.text(self.font, status, TEXT, (x, y))
        y += 32

        if self.message:
            self.text(self.small, self.message[:34], seat_color(0), (x, y))

        self.text(self.small, f"In play: {state.board.num_in_play}", TEXT_DIM, (x, height - 90))
        self.text(self.small, "R  new game", TEXT_DIM, (x, height - 62))
        self.text(self.small, "Q  quit", TEXT_DIM, (x, height - 38))

    def text(self, font: pygame.font.Font, text: str, color: tuple[int, int, int], pos: tuple[int, int]) -> None:
        self.screen.blit(font.render(text, True, color), pos)



# ---------------------------------------------------------------- entry point


def parse_args(argv: Sequence[str] | None = None) -> Namespace:
    parser = ArgumentParser(prog="nagrica-gui", description="Play Napoleon Grid Capture in a window.")

    add_game_args(parser)

    parser.add_argument(
        "-p", "--player",
        dest    = "players",
        action  = "append",
        type    = _player_spec,
        metavar = "TYPE[:OPTION...][=NAME]",
        help    = f"add a player, in turn order. Repeat for each player. "
                  f"Types: human, {', '.join(AI_TYPES)}. {AI_HELP} (default: human vs maxn)",
    )

    args = parser.parse_args(argv)

    if args.players is None:
        args.players = DEFAULT_PLAYERS

    if len(args.players) < 2:
        parser.error("at least 2 players are needed")

    return args


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)

    pygame.init()
    pygame.display.set_caption("Napoleon Grid Capture")

    try:
        App(args).run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
