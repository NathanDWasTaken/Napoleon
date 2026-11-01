from nagrica.grid           import Direction
from nagrica.grid.boards    import BitBoard




board = BitBoard(width = 3, height = 2)



board.place_wall((1, 0), Direction.NORTH)


"""


from nagrica.game           import CompleteGameState
from nagrica.grid           import Edge
from nagrica.ai             import Max_N, SimpleEval
from nagrica.capture        import GreedyCaptureDFS
from nagrica.settings       import GameSettings


gameState = CompleteGameState(
    height          = 4,
    width           = 4,
    num_players     = 2,
    capture_eval    = GreedyCaptureDFS,
    board_class     = BitBoard,
    settings        = GameSettings()
)






gameState.apply(Wall(
    Coord(2, 1), Direction.EAST
))


MAX_DEPTH = 5


search_algo = Max_N(SimpleEval(), max_depth=5)
search_algo._dfs_eval(gameState, MAX_DEPTH)


"""