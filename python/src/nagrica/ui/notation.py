"""
Game records, inspired by chess notation (SAN moves in a PGN file).

A move names a cell and the side of it the wall goes on: `b2N` is a wall on the north side of b2.
Columns are letters from the west (x = 0 is `a`, after `z` come `aa`, `ab`, ...),
rows are numbers from the south (y = 0 is `1`). Every wall is written from its south or west cell,
so `b2N` and `b3S` are the same move and both are written as `b2N`.

A record has tag pairs for the setup, then the moves numbered per round (one move per player):

    [Event "Napoleon Grid Capture"]
    [Date "2026.11.03"]
    [Height "3"]
    [Width "3"]
    [LastCell "next"]
    [Player1 "Alice"]
    [Player1Type "human"]
    [Player2 "Bob"]
    [Player2Type "maxn:3:margin(score)"]
    [Result "4-5"]

    1. a1N b2E 2. c1N a2E ...  4-5

Only moves are stored, captures follow from replaying them. Text in `{braces}` is a comment.
The result is the score per seat, or `*` for an unfinished game.
"""
import re

from dataclasses        import dataclass, field

from nagrica.grid       import Coord, Direction, Edge


MOVE_PATTERN    = re.compile(r"([a-z]+)(\d+)([NESW])", re.IGNORECASE)
TAG_PATTERN     = re.compile(r'\[(\w+)\s+"((?:[^"\\]|\\.)*)"\]')
NUMBER_PATTERN  = re.compile(r"\d+\.+")
RESULT_PATTERN  = re.compile(r"\*|\d+(?:-\d+)+")

LINE_WIDTH      = 80



class NotationError(ValueError):
    pass



# ---------------------------------------------------------------- moves


def column_name(x: int) -> str:
    """0 -> a, 25 -> z, 26 -> aa"""
    name = ""
    x   += 1

    while x:
        x, rest = divmod(x - 1, 26)
        name    = chr(ord("a") + rest) + name

    return name


def column_index(name: str) -> int:
    """a -> 0, z -> 25, aa -> 26"""
    x = 0

    for letter in name.lower():
        x = x * 26 + ord(letter) - ord("a") + 1

    return x - 1


def cell_name(coord: Coord) -> str:
    return f"{column_name(coord.x)}{coord.y + 1}"


def canonical(move: Edge) -> Edge:
    """The same wall, seen from its south or west cell"""
    if move.direction == Direction.SOUTH:
        return Edge(move.other, Direction.NORTH)

    if move.direction == Direction.WEST:
        return Edge(move.other, Direction.EAST)

    return move


def format_move(move: Edge) -> str:
    move = canonical(move)

    return f"{cell_name(move.coord)}{move.direction.name[0]}"


def parse_move(text: str) -> Edge:
    match = MOVE_PATTERN.fullmatch(text)

    if not match:
        raise NotationError(f"not a move: '{text}' (expected e.g. b2N)")

    column, row, direction = match.groups()

    if int(row) < 1:
        raise NotationError(f"rows start at 1, got '{text}'")

    return Edge(Coord(column_index(column), int(row) - 1), Direction.from_letter(direction))



# ---------------------------------------------------------------- records


@dataclass
class Record:
    height:     int
    width:      int
    last_cell:  str                                     # A key of `nagrica.cli.LAST_CELL`
    players:    list[tuple[str, str]]                   # (name, type) per seat, e.g. ("Bob", "maxn:3:score")
    moves:      list[Edge]              = field(default_factory=list)
    result:     str                     = "*"           # Scores per seat, e.g. `4-5`, or `*` when unfinished
    tags:       dict[str, str]          = field(default_factory=dict)  # Any other tags, e.g. Date


    @property
    def num_players(self) -> int:
        return len(self.players)



def _quote(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def _unquote(value: str) -> str:
    return re.sub(r"\\(.)", r"\1", value)


def format_record(record: Record) -> str:
    tags: dict[str, object] = {"Event": "Napoleon Grid Capture"} | record.tags
    tags |= {"Height": record.height, "Width": record.width, "LastCell": record.last_cell}

    for seat, (name, type_) in enumerate(record.players, start=1):
        tags[f"Player{seat}"]       = name
        tags[f"Player{seat}Type"]   = type_

    tags["Result"] = record.result

    header  = [f'[{key} "{_quote(value)}"]' for key, value in tags.items()]
    tokens  = []

    for index, move in enumerate(record.moves):
        if index % record.num_players == 0:
            tokens.append(f"{index // record.num_players + 1}.")

        tokens.append(format_move(move))

    tokens.append(record.result)

    return "\n".join(header) + "\n\n" + _wrap(tokens) + "\n"


def _wrap(tokens: list[str]) -> str:
    lines   = []
    line    = ""

    for token in tokens:
        if line and len(line) + 1 + len(token) > LINE_WIDTH:
            lines.append(line)
            line = token
        else:
            line = f"{line} {token}" if line else token

    lines.append(line)

    return "\n".join(lines)


def parse_record(text: str) -> Record:
    tags: dict[str, str] = {}
    body: list[str]      = []

    for line in text.splitlines():
        stripped = line.strip()

        if match := TAG_PATTERN.fullmatch(stripped):
            tags[match.group(1)] = _unquote(match.group(2))
        elif stripped:
            body.append(stripped)

    movetext    = re.sub(r"\{[^}]*\}", " ", " ".join(body))
    moves       = []

    for token in movetext.split():
        if NUMBER_PATTERN.fullmatch(token) or RESULT_PATTERN.fullmatch(token):
            continue

        moves.append(parse_move(token))

    try:
        height      = int(tags.pop("Height"))
        width       = int(tags.pop("Width"))
        last_cell   = tags.pop("LastCell")
    except KeyError as missing:
        raise NotationError(f"missing tag {missing}")
    except ValueError as error:
        raise NotationError(f"bad board size: {error}")

    players = []
    seat    = 1

    while f"Player{seat}" in tags:
        players.append((tags.pop(f"Player{seat}"), tags.pop(f"Player{seat}Type", "unknown")))
        seat += 1

    if len(players) < 2:
        raise NotationError("a record needs at least the tags Player1 and Player2")

    result = tags.pop("Result", "*")
    tags.pop("Event", None)

    return Record(height, width, last_cell, players, moves, result, tags)
