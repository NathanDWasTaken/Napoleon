from nagrica.grid       import Board
from .state             import GameState
from .player            import Player



class Match:
    finished        = False
    state:          GameState
    players:        list[Player]



    def __init__(
        self,
        players:        list[Player],
        height:         int,
        width:          int
    ) -> None:
        self.players        = players
        self.state          = GameState(height, width, len(players))


    @property
    def board(self) -> Board:
        return self.state.board


    def start(self):

        player_i = 0
        while not self.finished:
            player_i %= len(self.players)

            player  = self.players[player_i]
            move    = player.make_move(self.state.copy())

            self.state.apply(move, player_i)

            if len(self.board.in_play) == 0:
                self.finished = True

            player_i += 1




