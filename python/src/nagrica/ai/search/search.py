from abc            import ABC, abstractmethod

from ..eval.eval    import EvaluationAlgorithm
from nagrica.game   import GameState, Move




class SearchAlgorithm(ABC):
    eval_algo: EvaluationAlgorithm


    def __init__(self, eval_algo: EvaluationAlgorithm) -> None:
        self.eval_algo  = eval_algo
        


    @abstractmethod
    def select_move(self, gameState: GameState) -> Move:
        ...