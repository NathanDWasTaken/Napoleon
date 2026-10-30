from nagrica.game.state import GameState

from .eval      import EvaluationAlgorithm


class MarginEval(EvaluationAlgorithm):
    """Each player's value relative to the best opponent, on top of any evaluation"""
    base: EvaluationAlgorithm


    def __init__(self, base: EvaluationAlgorithm) -> None:
        self.base = base


    def evaluate(self, gameState: GameState) -> list[float]:
        vals = self.base.evaluate(gameState)


        return [
            val - max(vals[:i] + vals[i+1:])
            for i, val in enumerate(vals)
        ]