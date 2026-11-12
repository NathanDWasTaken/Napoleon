"""
Capture resolution on larger, more complex boards: `Board.seperated_region`
followed by `BasicGameState.calc_capture`, the same way `GameState.apply` does.

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

from nagrica.game                  import BasicGameState
from nagrica.grid.boards            import Board
from nagrica.grid.coord             import Coord
from nagrica.grid.direction         import Direction
from nagrica.grid.edge              import Edge
from nagrica.ui.text                import render_board


# ---------------------------------------------------------------- helpers


def board_from_ascii(board_class: type[Board], picture: str) -> tuple[Board, dict[str, set[Coord]]]:
    """
    Build a board from a `render_board`-style drawing.

    Cells labelled `x` are removed from play. Returns the board and, per label
    character, the coords carrying that label.
    """
    lines   = picture.strip("\n").splitlines()
    height  = (len(lines)   - 1) // 2
    width   = (len(lines[0]) - 1) // 4
    board   = board_class(height, width)
    labels: dict[str, set[Coord]] = {}

    assert len(lines) == 2 * height + 1, "picture needs a wall line above and below every row"

    for row in range(height):
        # NORTH is +y, so the first drawn row is the highest y
        y           = height - 1 - row
        wall_line   = lines[2 * row]
        content     = lines[2 * row + 1]

        for x in range(width):
            if row > 0 and wall_line[4 * x + 1 : 4 * x + 4] == "---":
                board.place_wall(Edge(Coord(x, y), Direction.NORTH))

            if x < width - 1 and content[4 * x + 4] == "|":
                board.place_wall(Edge(Coord(x, y), Direction.EAST))

            for char in content[4 * x + 1 : 4 * x + 4].strip():
                labels.setdefault(char, set()).add(Coord(x, y))

    board.capture(labels.get("x", set()))

    # Out of play regions were captured, so they must be walled off from the play area
    for coord in board.in_play:
        for neighbour in neighbours(board, coord):
            assert board.is_in_play(neighbour), f"{coord} is not walled off from out of play {neighbour}"

    return board, labels


def only(coords: set[Coord]) -> Coord:
    assert len(coords) == 1, f"expected exactly one cell, got {coords}"
    return next(iter(coords))


def neighbours(board: Board, coord: Coord) -> list[Coord]:
    """Every cell directly reachable from `coord`."""
    return [
        coord.to_neighbor(direction)
        for direction in Direction
        if board.connects(Edge(coord, direction))
    ]


def component(board: Board, start: Coord) -> set[Coord]:
    """Reference flood fill: every cell reachable from `start`."""
    seen    = {start}
    queue   = deque([start])

    while queue:
        for neighbour in neighbours(board, queue.popleft()):
            if neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)

    return seen


def state_for(board: Board) -> BasicGameState:
    """A game state playing on `board`, for resolving captures with the game's rules."""
    state       = BasicGameState(board.height, board.width, 2, board_class=type(board))
    state.board = board

    return state


def resolve(state: BasicGameState, start: Coord, goal: Coord) -> frozenset[Coord]:
    """The capture after a wall between `start` and `goal` was placed, the same way `GameState.apply` does."""
    return state.calc_capture(state.board.separated_region(start, goal)).coords


def play(state: BasicGameState, coord: Coord, direction: Direction) -> frozenset[Coord]:
    """Place a wall and apply its capture to the board."""
    state.board.place_wall(Edge(coord, direction))

    captured = resolve(state, coord, coord.to_neighbor(direction))
    state.board.capture(captured)

    return captured


# ---------------------------------------------------------------- helper sanity


def test_board_from_ascii_round_trips(board_class: type[Board]):
    picture = """
+---+---+---+---+
|       |       |
+   +---+   +   +
|   |           |
+   +   +---+---+
|               |
+---+---+---+---+
"""
    board, _ = board_from_ascii(board_class, picture)

    assert render_board(board) == picture.strip("\n")


# ---------------------------------------------------------------- reachability


def test_backtracks_out_of_dead_end(board_class: type[Board]):
    # Greedy search tries EAST before WEST, walking into the dead end first
    board, labels = board_from_ascii(board_class, """
+---+---+---+---+---+
|         G         |
+   +   +---+---+---+
|         S         |
+---+---+---+---+---+
""")
    assert resolve(state_for(board), only(labels["S"]), only(labels["G"])) == frozenset()


def test_reachable_through_serpentine(board_class: type[Board]):
    # S and G are neighbours, but the only path between them winds around the whole border
    board, labels = board_from_ascii(board_class, """
+---+---+---+---+
| S             |
+---+---+---+   +
| G |       |   |
+   +   +   +   +
|   |   |   |   |
+   +   +   +   +
|   |   |   |   |
+   +   +   +   +
|       |       |
+---+---+---+---+
""")
    assert resolve(state_for(board), only(labels["S"]), only(labels["G"])) == frozenset()


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
def test_captures_irregular_pocket(board_class: type[Board], from_label: str, to_label: str):
    # Whichever side the search starts on, the smaller region is captured
    board, labels = board_from_ascii(board_class, IRREGULAR_POCKET)

    captured = resolve(state_for(board), only(labels[from_label]), only(labels[to_label]))

    assert captured         == labels["#"]
    assert len(captured)    == 7


def test_captures_large_region_behind_long_wall(board_class: type[Board]):
    # The captured side is big (10 of 25) and only closes off with the final wall
    board, labels = board_from_ascii(board_class, """
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
    captured = resolve(state_for(board), only(labels["S"]), only(labels["G"]))

    assert captured         == labels["#"]
    assert len(captured)    == 10


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
def test_captures_against_shrunk_play_area(board_class: type[Board], from_label: str, to_label: str):
    # 12 cells are left in play, split 7 vs 5. The 7-cell side is under half of
    # the full board (16), but over half of the play area, so it must stay in play.
    board, labels = board_from_ascii(board_class, SHRUNK_PLAY_AREA)

    captured = resolve(state_for(board), only(labels[from_label]), only(labels[to_label]))

    assert captured == labels["#"]
    assert not captured & labels["x"]


# ---------------------------------------------------------------- game sequences


def test_captures_compare_against_remaining_play_area(board_class: type[Board]):
    # After the first capture only 12 cells are left. The final split is 7 vs 5:
    # the 7-cell side is under half of the full board (16), but over half of
    # what is still in play, so the 5-cell side must be the one captured.
    board   = board_class(4, 4)
    state   = state_for(board)
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
        captured = play(state, coord, direction)

        assert captured == expected, f"move {coord} {direction.name}\n{board}"

    assert board.num_in_play == 6


@pytest.mark.parametrize("height, width", [(2, 2), (3, 5), (5, 5), (6, 8)])
@pytest.mark.parametrize("seed", range(10))
def test_random_games_match_flood_fill(board_class: type[Board], height: int, width: int, seed: int):
    # Play random games to the end, checking every move against a brute-force flood fill
    rng     = Random(seed)
    board   = board_class(height, width)
    state   = state_for(board)

    while True:
        legal = [
            (coord, direction)
            for coord in sorted(board.in_play)
            for direction in (Direction.NORTH, Direction.EAST)
            if board.connects(Edge(coord, direction))
        ]
        if not legal:
            break

        coord, direction    = rng.choice(legal)
        goal                = coord.to_neighbor(direction)
        board.place_wall(Edge(coord, direction))

        start_side  = component(board, coord)
        goal_side   = component(board, goal)

        # The board reports either side of the split, the game picks the smaller side
        region = board.separated_region(coord, goal)

        if goal in start_side:
            assert region == set(), f"move {coord} {direction.name}\n{board}"
        else:
            assert region in (start_side, goal_side), f"move {coord} {direction.name}\n{board}"

        if goal in start_side:
            expected = set()
        elif len(start_side) <= len(goal_side):
            expected = start_side
        else:
            expected = goal_side

        captured = state.calc_capture(region).coords

        assert captured == expected, f"move {coord} {direction.name}\n{board}"

        board.capture(captured)

    # Every split hands out the smaller side, so the game always ends on one cell
    assert board.num_in_play == 1
