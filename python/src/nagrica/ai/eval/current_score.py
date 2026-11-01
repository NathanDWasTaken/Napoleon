from typing     import cast

from nagrica.game   import BasicGameState

from .eval          import EvaluationAlgorithm



class CurrentScore(EvaluationAlgorithm):
    def evaluate(self, gameState: BasicGameState) -> list[float]:
        return cast(list[float], gameState.scores.copy())