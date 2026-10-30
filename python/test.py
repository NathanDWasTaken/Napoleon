from nagrica.grid           import Coord, Direction
from nagrica.grid.boards    import LinkedBoard

from nagrica.game           import GameState, Move
from nagrica.players        import ComputerPlayer
from nagrica.ai             import Max_N, CurrentScore, SimpleEval
from nagrica.capture        import GreedyDFS
from nagrica.ui             import render_board
from nagrica.settings       import GameSettings


gameState = GameState(
    height          = 4,
    width           = 4,
    num_players     = 2,
    capture_eval    = GreedyDFS,
    board_class     = LinkedBoard,
    settings        = GameSettings()
)


gameState.apply(Move(
    Coord(2, 1), Direction.EAST
))


print(render_board(gameState.board))



computer = ComputerPlayer("CPU 1", 1, search_algo=Max_N(SimpleEval(), max_depth=3))

move = computer.make_move(gameState.copy())

gameState.apply(move)

print(render_board(gameState.board))

...