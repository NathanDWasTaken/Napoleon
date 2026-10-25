from .move              import Move
from .turn              import Turn
from .exceptions        import IllegalMove

from nagrica.grid       import Board, CoordLike
from nagrica.capture    import CaptureEvaluation, GreedyDFS


class GameState:
    board:          Board
    num_players:    int
    current_player: int
    scores:         list[int]

    # List of played moves. 
    history:        list[Turn]

    _ce:            type[CaptureEvaluation]
    

    def __init__(
        self,
        height:         int,
        width:          int,
        num_players:    int,
        *,
        capture_eval:   type[CaptureEvaluation] = GreedyDFS
    ):
        self.board          = Board(height, width)
        self.num_players    = num_players
        self.current_player = 0
        self.scores         = [0] * num_players
        self._ce            = capture_eval

    
    def is_legal(self, move: Move) -> bool:
        coord1 = move.coord
        coord2 = move.coord.to_neighbor(move.direction)

        # Check both cells still in play
        if not (coord1 in self.board.in_play and coord2 in self.board.in_play):
            return False

        return self.board.neighbor_is_reachable(coord1, move.direction)


    def legal_moves(self):
        """
        Generate all legal moves for the board
        """
        # TODO


    def copy(self) -> GameState:
        # TODO

        return self



    def apply(
        self,
        move:           Move,
        player_seat:    int,
    ):
        if not self.is_legal(move):
            raise IllegalMove(move, player_seat)

        coord       = move.coord
        direction   = move.direction


        self.board.place_wall(coord, direction)

        capture     = self.eval_capture(coord, coord.to_neighbor(direction))

        self.history.append(Turn(
            player_seat,
            move,
            capture
        ))

        # Skip if nothing was captured
        if not capture.coords:
            return

        self.scores[player_seat]    += capture.points
        self.board.register_capture(player_seat, capture.coords)
        self.board.in_play          -= capture.coords
    

    def undo(self):
        # TODO
        ...


    def eval_capture(self, start: CoordLike, end: CoordLike):
        ce      = self._ce(self.board)

        return ce.run(start, end)



