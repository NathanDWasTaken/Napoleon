from typing             import cast

from .turn              import Turn
from .exceptions        import IllegalMove

from nagrica.settings   import GameSettings, LastCellResolution
from nagrica.grid       import Board, Edge, Direction, Coord, CoordLike
from nagrica.capture    import Capture, CaptureEvaluation
from nagrica.exceptions import NagricaError


class BasicGameState:
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

    
    def is_legal(self, edge: Edge) -> bool:
        if not self.board.edge_is_valid(edge):
            return False

        return self.board.connects(edge)


    def legal_moves(self) -> list[Edge]:
        """
        Generate all legal moves for the board
        """
        all_moves: list[Edge] = []

        for coord in self.board.in_play:
            for direction in (Direction.NORTH, Direction.EAST):
                move = Edge(coord, direction)

                if not self.board.connects(move):
                    continue

                all_moves.append(move)

        return all_moves


    def apply(
        self,
        move:   Edge
    ):

        if not self.is_legal(move):
            raise IllegalMove(move, self.current_seat)


        self.board.place_wall(move)

        capture         = self.eval_capture(move.coord, move.other)
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
        if turn.wall is None:
            self._unregister_turn()


    def _unregister_turn(self) -> Turn:
        turn    = self.history.pop(-1)
        wall    = turn.wall
        capture = turn.capture
        seat    = turn.player_seat


        self.scores[seat] -= capture.points
        self.board.release(capture.coords)

        if wall is not None:
            self.board.remove_wall(wall)

        self._unregister_player_objects(wall, list(capture.coords))

        return turn

    def _unregister_player_objects(self, wall: Edge | None, captures: list[Coord]):
        """
        This function exists to unregister cells and walls belonging to players.
        This is seperated because the search algorithm does not need this information
        """


    def _register_turn(self, player_seat: int, wall: Edge | None, capture: Capture):
        if wall is None and not len(list(self.board.in_play)) == 1:
            raise NagricaError("Move of turn can only be None if this is the last Cell being given to the next person")

        self._register_player_objects(wall, list(capture.coords), player_seat)

        self.history.append(Turn(
            player_seat,
            wall,
            capture
        ))


        # If there was a capture, apply to board
        if capture.points:
            self.scores[player_seat] += capture.points
            self.board.capture(capture.coords)

        

    def _register_player_objects(self, wall: Edge | None, captures: list[Coord], seat: int):
        """
        This function exists to register cells and walls belonging to players.
        This is seperated because the search algorithm does not need this information
        """

    def eval_capture(self, start: CoordLike, end: CoordLike):
        ce      = self._ce(self.board)

        return ce.run(start, end)


    def copy(self):
        new = self.__new__(self.__class__)

        return self._overwrite_to(new)


    def _overwrite_to(self, other: BasicGameState):
        other.board       = self.board.copy()
        other.num_players = self.num_players
        other.scores      = self.scores.copy()
        other.history     = self.history.copy()
        other._ce         = self._ce
        other._settings   = self._settings

        return other




class CompleteGameState(BasicGameState):

    captured:   dict[Coord, int]
    placed:     dict[Edge, int]


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
        self.captured   = {}
        self.placed     = {}
        
        super().__init__(height, width, num_players, capture_eval=capture_eval, board_class=board_class, settings=settings)


    def copy(self) -> CompleteGameState:
        new             = cast(CompleteGameState, super().copy())
        new.captured    = self.captured.copy()
        new.placed      = self.placed.copy()

        return new


    def _unregister_player_objects(self, wall: Edge | None, captures: list[Coord]):

        if wall is not None:
            self.placed.pop(wall)
        
        for coord in captures:
            self.captured.pop(coord, None)


    def _register_player_objects(self, wall: Edge | None, captures: list[Coord], seat: int):
        if wall is not None:
            self.placed[wall] = seat

        for coord in captures:
            self.captured[coord] = seat


    def to_simple(self) -> BasicGameState:
        new = BasicGameState.__new__(BasicGameState)

        return self._overwrite_to(new)