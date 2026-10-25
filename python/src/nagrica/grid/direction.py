from enum           import Enum

from .vector       import Vector



class Direction(Vector[int], Enum):
    NORTH   = ( 0,  1 )
    EAST    = ( 1,  0 )
    SOUTH   = ( 0, -1 )
    WEST    = (-1,  0 )



N = Direction.NORTH
E = Direction.EAST
S = Direction.SOUTH
W = Direction.WEST