from abc            import ABC, abstractmethod


from nagrica.game   import BasicGameState



class EvaluationAlgorithm(ABC):
    @abstractmethod
    def evaluate(self, gameState: BasicGameState) -> list[float]:
        ...