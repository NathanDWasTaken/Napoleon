import re
from random         import choice

from nagrica.game   import Player, Move, GameState
from nagrica.grid   import Coord, Direction
from nagrica.ui     import render_board

from .exceptions    import InvalidInputPattern


class HumanPlayer(Player):

    HELP_TEXT = """
    The goal of the game is to capture as many tiles as possible.
    Per turn each player gets to play a single wall in the playable area of the grid.
    If this wall separates one or more tiles from the rest of the playable area,
    the player who placed the wall gets that area. 
    For each tile that a player captures, the player gets a point.

    To place a wall we use coordinates. These can be defined in 2 ways:
    - Coordinate and Cardinal Direction - X Y D
    Example: 0 1 N
    This means that we place the wall North of Tile at position X=0, Y=1
    - 2 Coordinates - X1 Y1 X2 Y2
    Example: 0 1 0 2
    This means that we place the wall between the tiles at position X=0, Y=1 and X=0, Y=2 
    """

    COORD_PATTERN       = r"[\(]?(\d+)[\s,-]+(\d+)[\)]?"
    DIRECTION_PATTERN   = r"([NESW])"
    INPUT_PATTERN_1     = COORD_PATTERN + r"\s+" + DIRECTION_PATTERN
    INPUT_PATTERN_2     = COORD_PATTERN + r"\s+" + COORD_PATTERN


    def _parse_input(self, user_input: str) -> Move:
        if   match := re.match(self.INPUT_PATTERN_1, user_input.upper()):
            x, y, d = match.groups()

            return Move(
                Coord(int(x), int(y)),
                Direction.from_letter(d)
            )

        elif match := re.match(self.INPUT_PATTERN_2, user_input.upper()):
            x1, y1, x2, y2 = match.groups()

            coord1      = Coord(int(x1), int(y1))
            coord2      = Coord(int(x2), int(y2))

            try:
                direction   = coord1.direction_to(coord2)
                
                return Move(
                    coord1,
                    direction
                )
            except ValueError:
                raise InvalidInputPattern(user_input)

        raise InvalidInputPattern(user_input)



    def make_move(self, gameState: GameState) -> Move:
        while True:
            print(render_board(gameState.board))
            print()
            print(f"{self.name} - Place a wall:")

            user_input = input("> ")

            if user_input.lower() in ("h", "help", "?"):
                print(self.HELP_TEXT)
                continue

            if user_input.lower() == "exit":
                raise KeyboardInterrupt()

            if user_input.lower() == "random":
                all_moves = gameState.legal_moves()
                return choice(all_moves)

            try:
                move = self._parse_input(user_input)
            except InvalidInputPattern:
                print(f"Could not parse input: {user_input} - Format needs to be (X Y D) or (X1 Y1 X2 Y2). Type help for more info")
                continue


            if gameState.is_legal(move):
                return move

            print("Move is Illegal!")
        