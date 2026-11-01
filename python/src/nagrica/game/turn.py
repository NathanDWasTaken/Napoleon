from dataclasses    import dataclass


from nagrica.grid       import Edge
from nagrica.capture    import Capture


@dataclass(frozen=True)
class Turn:
    player_seat:    int
    wall:           Edge | None
    capture:        Capture