from dataclasses    import dataclass
from enum           import Enum


class LastCellResolution(Enum):
    CURRENT_PLAYER  = 0
    NEXT_PLAYER     = 1



@dataclass(frozen=True)
class GameSettings:
    LASTCELLRESOLUTION: LastCellResolution = LastCellResolution.NEXT_PLAYER