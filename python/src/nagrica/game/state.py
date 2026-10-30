from .move              import Move
from .turn              import Turn
from .exceptions        import IllegalMove

from nagrica.settings   import GameSettings, LastCellResolution
from nagrica.grid       import Board, CoordLike, Direction
from nagrica.capture    import Capture, CaptureEvaluation
from nagrica.exceptions import NagricaError


class GameState:
    board:          Board
    num_players:    int
    scores:         list[int]

    # List of played moves. 
    history:        list[Turn]

    _ce:            type[CaptureEvaluation]
    _settings:      GameSettings
    

    def __init__(
        self,
        height:         int,
        width:          int,
        num_players:    int,
        *,
        capture_eval:   type[CaptureEvaluation],
        board_class:    type[Board],
        settings:       GameSettings    = GameSettings()
    ):
        self.board          = board_class(height, width)
        self.num_players    = num_players
        self.scores         = [0] * num_players
        self.history        = []

        self._ce            = capture_eval
        self._settings      = settings


    @property
    def finished(self):
        return self.board.num_in_play == 0

    @property
    def current_seat(self):
        return self.tick % self.num_players

    @property
    def tick(self):
        return len(self.history)

    
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
        new             = GameState.__new__(GameState)

        new.board       = self.board.copy()
        new.num_players = self.num_players
        new.scores      = self.scores.copy()
        new.history     = self.history.copy()
        new._ce         = self._ce
        new._settings   = self._settings

        return new



    def apply(
        self,
        move:           Move
    ):

        if not self.is_legal(move):
            raise IllegalMove(move, self.current_seat)

        coord       = move.coord
        direction   = move.direction


        self.board.place_wall(coord, direction)

        capture         = self.eval_capture(coord, coord.to_neighbor(direction))
        is_last_move    = capture.coords and (self.board.num_in_play == 2)


        if is_last_move and (self._settings.LASTCELLRESOLUTION == LastCellResolution.CURRENT_PLAYER):
            capture = Capture(frozenset(self.board.in_play))


        self._register_turn(self.current_seat, move, capture)

        
        # Register last cell to next player. This does not involve a move
        if is_last_move and (self._settings.LASTCELLRESOLUTION == LastCellResolution.NEXT_PLAYER):
            self._register_turn(
                self.current_seat,
                None,
                Capture(frozenset(self.board.in_play))
            )


    
    def undo(self):
        turn = self._unregister_turn()

        # Move is None if this was the last Cell given to the next player (LastCellResolution == NEXT_PLAYER).
        # That Turn came from the previous move, so undo that move as well
        if turn.move is None:
            self._unregister_turn()


    def _unregister_turn(self) -> Turn:
        turn    = self.history.pop(-1)
        move    = turn.move
        capture = turn.capture
        seat    = turn.player_seat


        self.scores[seat] -= capture.points
        self.board.release(capture.coords)

        if move is not None:
            self.board.remove_wall(move.coord, move.direction)

        return turn


    def _register_turn(self, player_seat: int, move: Move | None, capture: Capture):
        if move is None and not len(list(self.board.in_play)) == 1:
            raise NagricaError("Move of turn can only be None if this is the last Cell being given to the next person")

        self.history.append(Turn(
            player_seat,
            move,
            capture
        ))

        # If there was a capture, apply to board
        if capture.points:
            self.scores[player_seat] += capture.points
            self.board.capture(player_seat, capture.coords)

    


    def eval_capture(self, start: CoordLike, end: CoordLike):
        ce      = self._ce(self.board)

        return ce.run(start, end)



