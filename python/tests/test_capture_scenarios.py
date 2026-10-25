"""
Capture evaluation on larger, more complex boards.

Boards are drawn as ASCII art in the same format `render_board` produces.
Cell labels mark the move under test and the expected result:

    S   start of the move (the cell the wall is placed from)
    G   goal of the move (the cell on the other side of the wall)
    #   cell expected to be captured by this move
    x   cell captured on an earlier turn, already out of play

Drawings show the board after the move's wall has been placed.
"""
from collections    import deque
from random         import Random

import pytest

from nagrica.capture.capture         import CaptureEvaluation
from nagrica.capture.greedy_dfs      import GreedyDFS
from nagrica.grid.board              import Board
from nagrica.grid.coord              import Coord
from nagrica.grid.direction          import Direction
from nagrica.grid.render             import render_board


# Add new CaptureEvaluation implementations here to run every scenario against them
EVALUATORS = [GreedyDFS]


@pytest.fixture(params=EVALUATORS, ids=lambda cls: cls.__name__)
def evaluator(request: pytest.FixtureRequest) -> type[CaptureEvaluation]:
    return request.param


# ---------------------------------------------------------------- helpers


def board_from_ascii(picture: str) -> tuple[Board, dict[str, set[Coord]]]:
    """
    Build a board from a `render_board`-style drawing.

    Cells labelled `x` are removed from play. Returns the board and, per label
    character, the coords carrying that label.
    """
    lines   = picture.strip("\n").splitlines()
    height  = (len(lines)   - 1) // 2
    width   = (len(lines[0]) - 1) // 4
    board   = Board(height, width)
    labels: dict[str, set[Coord]] = {}

    assert len(lines) == 2 * height + 1, "picture needs a wall line above and below every row"

    for row in range(height):
        # NORTH is +y, so the first drawn row is the highest y
        y           = height - 1 - row
        wall_line   = lines[2 * row]
        content     = lines[2 * row + 1]

        for x in range(width):
            if row > 0 and wall_line[4 * x + 1 : 4 * x + 4] == "---":
                board.place_wall((x, y), Direction.NORTH)

            if x < width - 1 and content[4 * x + 4] == "|":
                board.place_wall((x, y), Direction.EAST)

            for char in content[4 * x + 1 : 4 * x + 4].strip():
                labels.setdefault(char, set()).add(Coord(x, y))

    board.in_play -= labels.get("x", set())

    # Out of play regions were captured, so they must be walled off from the play area
    for coord in board.in_play:
        for neighbour in board[coord].connections.values():
            assert neighbour.coord in board.in_play, f"{coord} is not walled off from out of play {neighbour.coord}"

    return board, labels


def only(coords: set[Coord]) -> Coord:
    assert len(coords) == 1, f"expected exactly one cell, got {coords}"
    return next(iter(coords))


def component(board: Board, start: Coord) -> set[Coord]:
    """Reference flood fill: every cell reachable from `start`."""
    seen    = {start}
    queue   = deque([start])

    while queue:
        cell = board[queue.popleft()]

        for neighbour in cell.connections.values():
            if neighbour.coord not in seen:
                seen.add(neighbour.coord)
                queue.append(neighbour.coord)

    return seen


def play(board: Board, evaluator: CaptureEvaluation, coord: Coord, direction: Direction) -> frozenset[Coord]:
    """Place a wall and resolve the capture, the same way `Match.handle_player_move` does."""
    board.place_wall(coord, direction)

    captured        = evaluator.run(coord, coord.to_neighbor(direction)).coords
    board.in_play  -= captured

    return captured


# ---------------------------------------------------------------- helper sanity


def test_board_from_ascii_round_trips():
    picture = """
+---+---+---+---+
|       |       |
+   +---+   +   +
|   |           |
+   +   +---+---+
|               |
+---+---+---+---+
"""
    board, _ = board_from_ascii(picture)

    assert render_board(board) == picture.strip("\n")


# ---------------------------------------------------------------- reachability


def test_backtracks_out_of_dead_end(evaluator: type[CaptureEvaluation]):
    # Greedy search tries EAST before WEST, walking into the dead end first
    board, labels = board_from_ascii("""
+---+---+---+---+---+
|         G         |
+   +   +---+---+---+
|         S         |
+---+---+---+---+---+
""")
    result = evaluator(board).run(only(labels["S"]), only(labels["G"]))

    assert not result.split


def test_reachable_through_serpentine(evaluator: type[CaptureEvaluation]):
    # The only path from S to G winds through every row of the board
    board, labels = board_from_ascii("""
+---+---+---+---+---+
| G                 |
+   +---+---+---+---+
|                   |
+---+---+---+---+   +
|                   |
+   +---+---+---+---+
|                   |
+---+---+---+---+   +
| S                 |
+---+---+---+---+---+
""")
    result = evaluator(board).run(only(labels["S"]), only(labels["G"]))

    assert not result.split


# ---------------------------------------------------------------- captures


IRREGULAR_POCKET = """
+---+---+---+---+---+
| # | #   # |       |
+   +---+   +   +   +
| #   #   # |       |
+   +---+---+   +   +
| G#|               |
+---+   +   +   +   +
| S                 |
+   +   +   +   +   +
|                   |
+---+---+---+---+---+
"""


@pytest.mark.parametrize("from_label, to_label", [("S", "G"), ("G", "S")], ids=["from-large-side", "from-small-side"])
def test_captures_irregular_pocket(evaluator: type[CaptureEvaluation], from_label: str, to_label: str):
    # Whichever side the search starts on, the smaller region is captured
    board, labels = board_from_ascii(IRREGULAR_POCKET)

    result = evaluator(board).run(only(labels[from_label]), only(labels[to_label]))

    assert result.coords  == labels["#"]
    assert result.points    == 7


def test_captures_large_region_behind_long_wall(evaluator: type[CaptureEvaluation]):
    # The captured side is big (10 of 25) and only closes off with the final wall
    board, labels = board_from_ascii("""
+---+---+---+---+---+
| #   #   #   #   # |
+   +   +   +   +   +
| #   # | G#| #   # |
+---+---+---+---+---+
|         S         |
+   +   +   +   +   +
|                   |
+   +   +   +   +   +
|                   |
+---+---+---+---+---+
""")
    result = evaluator(board).run(only(labels["S"]), only(labels["G"]))

    assert result.coords  == labels["#"]
    assert result.points    == 10


SHRUNK_PLAY_AREA = """
+---+---+---+---+
| x | #   #   # |
+   +---+   +   +
| x |   | #   G#|
+   +   +---+---+
| x |         S |
+   +   +   +   +
| x |           |
+---+---+---+---+
"""


@pytest.mark.parametrize("from_label, to_label", [("S", "G"), ("G", "S")], ids=["from-large-side", "from-small-side"])
def test_captures_against_shrunk_play_area(evaluator: type[CaptureEvaluation], from_label: str, to_label: str):
    # 12 cells are left in play, split 7 vs 5. The 7-cell side is under half of
    # the full board (16), but over half of the play area, so it must stay in play.
    board, labels = board_from_ascii(SHRUNK_PLAY_AREA)

    result = evaluator(board).run(only(labels[from_label]), only(labels[to_label]))

    assert result.coords  == labels["#"]
    assert not result.coords & labels["x"]


# ---------------------------------------------------------------- game sequences


def test_captures_compare_against_remaining_play_area(evaluator: type[CaptureEvaluation]):
    # After the first capture only 12 cells are left. The final split is 7 vs 5:
    # the 7-cell side is under half of the full board (16), but over half of
    # what is still in play, so the 5-cell side must be the one captured.
    board   = Board(4, 4)
    dfs     = evaluator(board)
    N, E, S = Direction.NORTH, Direction.EAST, Direction.SOUTH

    moves = [
        # Seal off the west column
        (Coord(0, 0), E, set()),
        (Coord(0, 1), E, set()),
        (Coord(0, 2), E, set()),
        (Coord(0, 3), E, {Coord(0, 0), Coord(0, 1), Coord(0, 2), Coord(0, 3)}),

        # Split the remaining 12 cells into 7 (south) and 5 (north)
        (Coord(1, 2), N, set()),
        (Coord(1, 2), E, set()),
        (Coord(2, 1), N, set()),
        (Coord(3, 1), N, {Coord(2, 2), Coord(3, 2), Coord(1, 3), Coord(2, 3), Coord(3, 3)}),

        # Cut a single cell off what is left
        (Coord(1, 2), S, {Coord(1, 2)}),
    ]

    for coord, direction, expected in moves:
        captured = play(board, dfs, coord, direction)

        assert captured == expected, f"move {coord} {direction.name}\n{board}"

    assert len(board.in_play) == 6


@pytest.mark.parametrize("height, width", [(2, 2), (3, 5), (5, 5), (6, 8)])
@pytest.mark.parametrize("seed", range(10))
def test_random_games_match_flood_fill(evaluator: type[CaptureEvaluation], height: int, width: int, seed: int):
    # Play random games to the end, checking every move against a brute-force flood fill
    rng     = Random(seed)
    board   = Board(height, width)
    dfs     = evaluator(board)

    while True:
        legal = [
            (coord, direction)
            for coord in sorted(board.in_play)
            for direction in (Direction.NORTH, Direction.EAST)
            if board[coord].connects(direction)
        ]
        if not legal:
            break

        coord, direction    = rng.choice(legal)
        goal                = coord.to_neighbor(direction)
        board.place_wall(coord, direction)

        start_side  = component(board, coord)
        goal_side   = component(board, goal)

        if goal in start_side:
            expected = set()
        elif len(start_side) <= len(goal_side):
            expected = start_side
        else:
            expected = goal_side

        captured = dfs.run(coord, goal).coords

        assert captured == expected, f"move {coord} {direction.name}\n{board}"

        board.in_play -= captured

    # Every split hands out the smaller side, so the game always ends on one cell
    assert len(board.in_play) == 1
