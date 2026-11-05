from pyinstrument           import Profiler
from pyinstrument.renderers import SpeedscopeRenderer

from pathlib                import Path

from nagrica.grid.boards    import LinkedBoard, BitBoard

from nagrica.game           import CompleteGameState
from nagrica.ai             import Max_N, SimpleEval, MarginEval, RandomMove
from nagrica.settings       import GameSettings
from nagrica.ui             import render_board


SEED        = 1
N_MOVES     = 4
MAX_DEPTH   = 5



gameState = CompleteGameState(
    height          = 4,
    width           = 4,
    num_players     = 2,
    board_class     = BitBoard,
    settings        = GameSettings()
)


random = RandomMove(seed = SEED)


for _ in range(N_MOVES):
    gameState.apply(random.select_move(gameState))

print(render_board(gameState.board, owners=gameState.captured))

search_algo = Max_N(MarginEval(SimpleEval()), max_depth=3)

profiler = Profiler()
profiler.start()
search_algo._dfs_eval(gameState.to_simple(), MAX_DEPTH)
profiler.stop()


renderer = SpeedscopeRenderer(processor_options={"filter_threshold": 0})
with open(Path(__file__).parent / "profile.speedscope.json", "w") as f:
    f.write(renderer.render(profiler.last_session))
...