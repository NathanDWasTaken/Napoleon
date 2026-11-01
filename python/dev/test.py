from nagrica.grid           import Edge, Coord, Direction
from nagrica.grid.boards    import LinkedBoard

from nagrica.game           import CompleteGameState
from nagrica.players        import ComputerPlayer
from nagrica.ai             import Max_N, SimpleEval
from nagrica.capture        import GreedyCaptureDFS
from nagrica.ui             import render_board
from nagrica.settings       import GameSettings


gameState = CompleteGameState(
    height          = 4,
    width           = 4,
    num_players     = 2,
    capture_eval    = GreedyCaptureDFS,
    board_class     = LinkedBoard,
    settings        = GameSettings()
)


gameState.apply(Edge(
    Coord(2, 1), Direction.EAST
))


print(render_board(gameState.board))



computer = ComputerPlayer("CPU 1", 1, search_algo=Max_N(SimpleEval(), max_depth=5, max_time=None))

move = computer.make_move(gameState.copy())

gameState.apply(move)

print(render_board(gameState.board))

...