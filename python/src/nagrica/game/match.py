from .state     import CompleteGameState
from .player    import Player

from nagrica.settings       import GameSettings
from nagrica.grid.boards    import Board, LinkedBoard


class Match:
    state:      CompleteGameState
    players:    list[Player]


    def __init__(
        self,
        players:        list[Player],
        height:         int,
        width:          int,
        *,
        board_class:    type[Board]             = LinkedBoard,
        settings:       GameSettings            = GameSettings(),
    ) -> None:
        self.players        = players
        self.state          = CompleteGameState(
            height,
            width,
            len(players),
            board_class     = board_class,
            settings        = settings,
        )


    @property
    def current_seat(self) -> int:
        return self.state.current_seat

    @property
    def current_player(self) -> Player:
        return self.players[self.state.current_seat]



    def game_loop(self):

        while not self.state.finished:
            player  = self.current_player
            move    = player.make_move(self.state.copy())

            self.state.apply(move)
