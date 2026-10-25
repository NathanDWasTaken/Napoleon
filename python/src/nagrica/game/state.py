from .move              import Move
from .turn              import Turn
from .exceptions        import IllegalMove

from nagrica.grid       import Board, CoordLike, Direction
from nagrica.capture    import Capture, CaptureEvaluation


class GameState:
    board:          Board
    num_players:    int
    scores:         list[int]

    # List of played moves. 
    history:        list[Turn]

    _tick:          int     = 0
    _ce:            type[CaptureEvaluation]
    

    def __init__(
        self,
        height:         int,
        width:          int,
        num_players:    int,
        *,
        capture_eval:   type[CaptureEvaluation],
        board_class:    type[Board],
    ):
        self.board          = board_class(height, width)
        self.num_players    = num_players
        self.scores         = [0] * num_players
        self.history        = []

        self._ce            = capture_eval


    @property
    def finished(self):
        return self.board.num_in_play == 0

    @property
    def current_seat(self):
        return self._tick % self.num_players

    
    def is_legal(self, move: Move) -> bool:
        coord1  = move.coord
        coord2  = move.coord.to_neighbor(move.direction)
        b       = self.board

        # Check both cells still in play
        if not (b.is_in_play(coord1) and b.is_in_play(coord2)):
            return False

        return self.board.connects(coord1, move.direction)


    def legal_moves(self) -> list[Move]:
        """
        Generate all legal moves for the board
        """
        all_moves: list[Move] = []

        for coord in self.board.in_play:
            for direction in (Direction.NORTH, Direction.EAST):
                if not self.board.connects(coord, direction):
                    continue

                all_moves.append(Move(
                    coord, direction
                ))

        return all_moves


    def copy(self) -> GameState:
        # TODO

        return self



    def apply(
        self,
        move:           Move
    ):

        if not self.is_legal(move):
            raise IllegalMove(move, self.current_seat)

        coord       = move.coord
        direction   = move.direction


        self.board.place_wall(coord, direction)

        capture     = self.eval_capture(coord, coord.to_neighbor(direction))


        if capture.coords:
            if self.board.num_in_play == 2:
                capture = Capture(frozenset(self.board.in_play))

            self._register_capture(self.current_seat, capture)

        self._register_move(move, capture)


    def _register_move(self, move: Move, capture: Capture):
        self.history.append(Turn(
            self.current_seat,
            move,
            capture
        ))
        self._tick += 1


    def _register_capture(self, player_seat: int, capture: Capture):
        self.scores[player_seat]    += capture.points
        self.board.capture(player_seat, capture.coords)

    

    def undo(self):
        # TODO
        ...


    def eval_capture(self, start: CoordLike, end: CoordLike):
        ce      = self._ce(self.board)

        return ce.run(start, end)



