from nagrica.game   import Player, Move, GameState


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


    def make_move(self, gameState: GameState) -> Move:
        return self.search_algo.select_move(gameState)
