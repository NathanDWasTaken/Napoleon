from typing         import cast

from nagrica.game   import BasicGameState
from nagrica.ui     import render_board

from .eval          import EvaluationAlgorithm


def render_state(state: BasicGameState):
    print(render_board(state.board))



class SimpleEval(EvaluationAlgorithm):
    def evaluate(self, gameState: BasicGameState) -> list[float]:
        return cast(list[float], gameState.scores.copy())