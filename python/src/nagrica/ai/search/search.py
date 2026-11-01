from abc    import ABC, abstractmethod

from nagrica.ai.eval    import EvaluationAlgorithm
from nagrica.game       import BasicGameState
from nagrica.grid       import Edge




class SearchAlgorithm(ABC):
    eval_algo: EvaluationAlgorithm


    def __init__(self, eval_algo: EvaluationAlgorithm) -> None:
        self.eval_algo  = eval_algo
        


    @abstractmethod
    def select_move(self, gameState: BasicGameState) -> Edge:
        ...