from nagrica.grid.boards         import Board
from nagrica.grid.coord          import Coord
from nagrica.grid.direction      import Direction
from nagrica.ui.text             import render_board


def test_empty_board(board_class: type[Board]):
    # Deliberately not square, so height and width can't be mixed up
    board = board_class(height=2, width=3)

    assert render_board(board) == "\n".join([
        "+---+---+---+",
        "|           |",
        "+   +   +   +",
        "|           |",
        "+---+---+---+",
    ])


def test_owned_cells_and_walls(board_class: type[Board]):
    board = board_class(3, 3)

    board.capture(1, {Coord(0, 0)})
    board.capture(9, {Coord(2, 2)})
    board.place_wall((1, 1), Direction.EAST)
    board.place_wall((1, 1), Direction.NORTH)

    assert render_board(board) == "\n".join([
        "+---+---+---+",
        "|         9 |",
        "+   +---+   +",
        "|       |   |",
        "+   +   +   +",
        "| 1         |",
        "+---+---+---+",
    ])


def test_north_is_printed_on_top(board_class: type[Board]):
    board = board_class(2, 1)
    board.capture(7, {Coord(0, 1)})

    assert render_board(board).splitlines()[1] == "| 7 |"


def test_labels(board_class: type[Board]):
    board = board_class(2, 2)

    assert render_board(board, {Coord(0, 0): "a", Coord(1, 1): "b"}) == "\n".join([
        "+---+---+",
        "|     b |",
        "+   +   +",
        "| a     |",
        "+---+---+",
    ])


def test_labels_override_owner(board_class: type[Board]):
    board = board_class(1, 1)
    board.capture(3, {Coord(0, 0)})

    assert render_board(board, {Coord(0, 0): "x"}).splitlines()[1] == "| x |"


def test_cell_width(board_class: type[Board]):
    board = board_class(1, 2)
    board.capture(4, {Coord(1, 0)})

    assert render_board(board, cell_width=5) == "\n".join([
        "+-----+-----+",
        "|        4  |",
        "+-----+-----+",
    ])


# ---------------------------------------------------------------- axes


def test_axes(board_class: type[Board]):
    board = board_class(height=2, width=3)

    assert render_board(board, axes=True) == "\n".join([
        "    0   1   2",
        "  +---+---+---+",
        "1 |           | 1",
        "  +   +   +   +",
        "0 |           | 0",
        "  +---+---+---+",
        "    0   1   2",
    ])


def test_axes_pad_multi_digit_rows(board_class: type[Board]):
    lines = render_board(board_class(11, 1), axes=True).splitlines()

    assert lines[0]     == "     0"
    assert lines[1]     == "   +---+"
    assert lines[2]     == "10 |   | 10"
    assert lines[-3]    == " 0 |   | 0"
    assert lines[-1]    == "     0"


def test_axes_follow_cell_width(board_class: type[Board]):
    board = board_class(1, 2)

    assert render_board(board, cell_width=5, axes=True) == "\n".join([
        "     0     1",
        "  +-----+-----+",
        "0 |           | 0",
        "  +-----+-----+",
        "     0     1",
    ])


def test_axes_are_off_by_default(board_class: type[Board]):
    # The plain drawing is also the format the capture scenario tests parse
    assert render_board(board_class(2, 2)).splitlines()[0] == "+---+---+"
