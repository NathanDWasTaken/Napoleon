from dataclasses    import dataclass


from nagrica.grid       import Coord, Direction


@dataclass(frozen=True)
class Move:
    coord:      Coord
    direction:  Direction