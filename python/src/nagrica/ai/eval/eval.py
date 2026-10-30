from abc            import ABC, abstractmethod


from nagrica.game   import GameState



class EvaluationAlgorithm(ABC):
    @abstractmethod
    def evaluate(self, gameState: GameState) -> list[float]:
        ...