from .state             import GameState
from .player            import Player

from nagrica.capture        import CaptureEvaluation, GreedyDFS
from nagrica.grid.boards    import Board, LinkedBoard



class Match:
    state:      GameState
    players:    list[Player]



    def __init__(
        self,
        players:        list[Player],
        height:         int,
        width:          int,
        *,
        capture_eval:   type[CaptureEvaluation] = GreedyDFS,
        board_class:    type[Board]             = LinkedBoard,
    ) -> None:
        self.players        = players
        self.state          = GameState(
            height,
            width,
            len(players),
            capture_eval    = capture_eval,
            board_class     = board_class
        )


    @property
    def current_seat(self) -> int:
        return self.state.current_seat

    @property
    def current_player(self) -> Player:
        return self.players[self.state.current_seat]




    def start(self):

        while not self.state.finished:
            player  = self.current_player
            move    = player.make_move(self.state.copy())

            self.state.apply(move)
