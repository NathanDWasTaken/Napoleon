from nagrica.game   import Player, CompleteGameState
from nagrica.grid   import Edge

from nagrica.ai     import SearchAlgorithm



class ComputerPlayer(Player):
    # The search owns its evaluation algorithm, if it uses one
    search_algo:    SearchAlgorithm



    def __init__(
        self,
        name: str,
        seat: int,
        *,
        search_algo:    SearchAlgorithm
    ) -> None:
        self.search_algo    = search_algo


        super().__init__(name, seat)


    def make_move(self, gameState: CompleteGameState) -> Edge:
        return self.search_algo.select_move(gameState.to_simple())
