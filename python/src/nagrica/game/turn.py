from dataclasses    import dataclass

from .capture       import Capture
from nagrica.grid   import Edge


@dataclass(frozen=True)
class Turn:
    player_seat:    int
    wall:           Edge | None
    capture:        Capture