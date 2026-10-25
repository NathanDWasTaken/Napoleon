from nagrica.grid.board          import Board
from nagrica.grid.coord          import Coord
from nagrica.grid.direction      import Direction
from nagrica.grid.render         import render_board


def test_empty_board():
    # Deliberately not square, so height and width can't be mixed up
    board = Board(height=2, width=3)

    assert render_board(board) == "\n".join([
        "+---+---+---+",
        "|           |",
        "+   +   +   +",
        "|           |",
        "+---+---+---+",
    ])


def test_owned_cells_and_walls():
    board = Board(3, 3)

    board[(0, 0)].owned = 1
    board[(2, 2)].owned = 9
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


def test_north_is_printed_on_top():
    board = Board(2, 1)
    board[(0, 1)].owned = 7

    assert render_board(board).splitlines()[1] == "| 7 |"


def test_labels():
    board = Board(2, 2)

    assert render_board(board, {Coord(0, 0): "a", Coord(1, 1): "b"}) == "\n".join([
        "+---+---+",
        "|     b |",
        "+   +   +",
        "| a     |",
        "+---+---+",
    ])


def test_labels_override_owner():
    board = Board(1, 1)
    board[(0, 0)].owned = 3

    assert render_board(board, {Coord(0, 0): "x"}).splitlines()[1] == "| x |"


def test_cell_width():
    board = Board(1, 2)
    board[(1, 0)].owned = 4

    assert render_board(board, cell_width=5) == "\n".join([
        "+-----+-----+",
        "|        4  |",
        "+-----+-----+",
    ])
