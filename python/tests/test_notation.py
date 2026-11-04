import pytest

from nagrica.grid               import Coord, Direction, Edge
from nagrica.ui.notation        import (
    NotationError, Record,
    canonical, cell_name, column_index, column_name,
    format_move, format_record, parse_move, parse_record,
)


N, E, S, W = Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST


# ---------------------------------------------------------------- moves


@pytest.mark.parametrize("x, name", [(0, "a"), (1, "b"), (25, "z"), (26, "aa"), (27, "ab"), (51, "az"), (52, "ba"), (701, "zz"), (702, "aaa")])
def test_column_names(x: int, name: str):
    assert column_name(x)       == name
    assert column_index(name)   == x


def test_cell_name_counts_rows_from_one():
    assert cell_name(Coord(0, 0)) == "a1"
    assert cell_name(Coord(2, 4)) == "c5"


@pytest.mark.parametrize("move, text", [
    (Edge(Coord(1, 1), N), "b2N"),
    (Edge(Coord(1, 1), E), "b2E"),
    (Edge(Coord(1, 2), S), "b2N"),
    (Edge(Coord(2, 1), W), "b2E"),
])
def test_format_move_writes_from_south_or_west_cell(move: Edge, text: str):
    assert format_move(move) == text


def test_canonical_keeps_the_same_wall():
    for direction in Direction:
        move = Edge(Coord(3, 3), direction)

        wall = canonical(move)

        assert {wall.coord, wall.other} == {move.coord, move.other}
        assert wall.direction           in (N, E)


@pytest.mark.parametrize("text, move", [
    ("a1N",  Edge(Coord(0, 0), N)),
    ("c4e",  Edge(Coord(2, 3), E)),
    ("B2S",  Edge(Coord(1, 1), S)),
    ("aa10W", Edge(Coord(26, 9), W)),
])
def test_parse_move(text: str, move: Edge):
    assert parse_move(text) == move


@pytest.mark.parametrize("text", ["", "a1", "1aN", "a0N", "a1X", "a1NN", "(0, 0) N"])
def test_parse_move_rejects(text: str):
    with pytest.raises(NotationError):
        parse_move(text)


def test_format_then_parse_round_trips():
    for x in range(30):
        for y in range(3):
            for direction in (N, E):
                move = Edge(Coord(x, y), direction)

                assert parse_move(format_move(move)) == move



# ---------------------------------------------------------------- records


def make_record(moves: int = 5, players: int = 2) -> Record:
    walls = [Edge(Coord(x, 0), N) for x in range(moves)]

    return Record(
        height      = 2,
        width       = moves,
        last_cell   = "next",
        players     = [(f"P{seat}", "random") for seat in range(players)],
        moves       = walls,
        result      = "3-7",
        tags        = {"Date": "2026.11.03"},
    )


def test_format_record_layout():
    text = format_record(make_record(3))

    assert text == "\n".join([
        '[Event "Napoleon Grid Capture"]',
        '[Date "2026.11.03"]',
        '[Height "2"]',
        '[Width "3"]',
        '[LastCell "next"]',
        '[Player1 "P0"]',
        '[Player1Type "random"]',
        '[Player2 "P1"]',
        '[Player2Type "random"]',
        '[Result "3-7"]',
        '',
        '1. a1N b1N 2. c1N 3-7',
        '',
    ])


def test_move_numbers_count_rounds_of_all_players():
    text = format_record(make_record(7, players=3))

    assert text.splitlines()[-1] == "1. a1N b1N c1N 2. d1N e1N f1N 3. g1N 3-7"


@pytest.mark.parametrize("moves, players", [(0, 2), (1, 2), (8, 2), (100, 3)])
def test_record_round_trips(moves: int, players: int):
    record = make_record(moves, players)

    assert parse_record(format_record(record)) == record


def test_long_games_are_wrapped():
    text = format_record(make_record(100))

    assert all(len(line) <= 80 for line in text.splitlines())


def test_names_with_quotes_round_trip():
    record          = make_record()
    record.players  = [('Al "the wall" \\o/', "human"), ("Bob", "human")]

    assert parse_record(format_record(record)).players == record.players


def test_parse_ignores_comments_and_extra_whitespace():
    record = parse_record('''
        [Height "2"]
        [Width "2"]
        [LastCell "current"]
        [Player1 "A"]
        [Player2 "B"]

        1. a1N {opening} a1E
        2.   b1N  *
    ''')

    assert record.moves     == [Edge(Coord(0, 0), N), Edge(Coord(0, 0), E), Edge(Coord(1, 0), N)]
    assert record.result    == "*"
    assert record.players   == [("A", "unknown"), ("B", "unknown")]
    assert record.last_cell == "current"


def test_parse_keeps_unknown_tags():
    record = parse_record('[Height "1"]\n[Width "2"]\n[LastCell "next"]\n[Player1 "A"]\n[Player2 "B"]\n[Site "home"]\n\n1. a1E *')

    assert record.tags == {"Site": "home"}


@pytest.mark.parametrize("text", [
    '[Width "2"]\n[LastCell "next"]\n[Player1 "A"]\n[Player2 "B"]',
    '[Height "x"]\n[Width "2"]\n[LastCell "next"]\n[Player1 "A"]\n[Player2 "B"]',
    '[Height "2"]\n[Width "2"]\n[LastCell "next"]\n[Player1 "A"]',
    '[Height "2"]\n[Width "2"]\n[LastCell "next"]\n[Player1 "A"]\n[Player2 "B"]\n\n1. a1N zz',
], ids=["missing-height", "bad-height", "one-player", "bad-move"])
def test_parse_record_rejects(text: str):
    with pytest.raises(NotationError):
        parse_record(text)
