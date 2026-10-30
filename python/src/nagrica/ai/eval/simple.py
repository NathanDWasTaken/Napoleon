from typing         import cast

from nagrica.game   import GameState
from nagrica.ui     import render_board

from .eval          import EvaluationAlgorithm


def render_state(state: GameState):
    print(render_board(state.board))



class SimpleEval(EvaluationAlgorithm):
    def evaluate(self, gameState: GameState) -> list[float]:
        return cast(list[float], gameState.scores.copy())