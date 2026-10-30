from typing     import cast

from nagrica.game   import GameState

from .eval          import EvaluationAlgorithm



class CurrentScore(EvaluationAlgorithm):
    def evaluate(self, gameState: GameState) -> list[float]:
        return cast(list[float], gameState.scores.copy())