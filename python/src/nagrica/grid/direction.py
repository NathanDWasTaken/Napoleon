from enum           import Enum

from .vector       import Vector



class Direction(Vector[int], Enum):
    NORTH   = ( 0,  1 )
    EAST    = ( 1,  0 )
    SOUTH   = ( 0, -1 )
    WEST    = (-1,  0 )

    @classmethod
    def from_letter(cls, letter: str) -> Direction:
        return next(d for d in cls if d.name[0] == letter.upper())



N = Direction.NORTH
E = Direction.EAST
S = Direction.SOUTH
W = Direction.WEST