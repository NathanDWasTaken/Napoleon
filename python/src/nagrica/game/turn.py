from dataclasses    import dataclass


from .move              import Move
from nagrica.capture    import Capture


@dataclass(frozen=True)
class Turn:
    player_seat:    int
    move:           Move | None
    capture:        Capture