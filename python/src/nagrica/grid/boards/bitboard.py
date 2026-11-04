from typing     import Iterable, Self

from .board     import Board

from nagrica.grid.direction     import Direction, N, E, S, W    
from nagrica.grid.coord         import Coord, CoordLike
from nagrica.grid.edge          import Edge


class BitBoard(Board):


    # Bitmask for connected cells
    _connections:   int

    # We encode connections as follows:
    # - Each and every cell gets its North and East connection defined
    # - Instead of leaving out connections that are impossible from the bitmask (Such as N at the very top or E at the very right)
    #   We just set those values to 0 from the getgo

    # Connections for each cell is stored using 2 bits, the connection South and the connection East.
    # row h:  w-1 - Horizontal
    # row x: 2w-1 - Vertical + Horizontal


    num_conn_per_row:   int
    num_connections:    int

    board_mask:         int
    neighbor_mask:      int

    dir_masks:          dict[Direction, int]
        

    def build_board(self, height: int, width: int):
        # Number of connections (N and E) per row
        self.num_conn_per_row   = 2 * width

        # Total number of connections 
        self.num_connections    = self.num_conn_per_row * height

        self.board_mask         = (1 << self.num_connections) -1

        self.dir_masks          = {}
        self.dir_masks[N]       = 1 << self.num_connections
        self.dir_masks[E]       =  self.dir_masks[N] << 1
        self.dir_masks[W]       =  self.dir_masks[N] >> 1
        self.dir_masks[S]       =  self.dir_masks[N] >> self.num_conn_per_row

        self.neighbor_mask      = self.dir_masks[N] | self.dir_masks[E] | self.dir_masks[W] | self.dir_masks[S]


        # Set impossible connections to 0:
        # - North   at the very top
        # - East    at the very right
        unreachable_east_row    = "0" + "1" * (2 * width - 1)
        unreachable_east        = int(unreachable_east_row * height, base=2)
        unreachable_north_row   = "10" * width
        unreachable_north       = int(unreachable_north_row + "11" * width * (height - 1), base=2)

        # There cannot be an overlap of unreachable east & unreachable north bits
        assert self._flip_bits(unreachable_east) & self._flip_bits(unreachable_north) == 0

        self._connections       = unreachable_east & unreachable_north


    # Do and Undo actions

    def place_wall(self, wall: Edge):
        self.ensure_valid_edge(wall)

        pos = self._get_pos(wall.coord, wall.direction)

        self._connections &= self.board_mask - (2 ** pos)



    def remove_wall(self, wall: Edge):
        self.ensure_valid_edge(wall)

        pos = self._get_pos(wall.coord, wall.direction)

        self._connections |= 2 ** pos


    # Helper functions

    def connects(self, edge: Edge) -> bool:
        if not self.edge_is_valid(edge):
            return False

        pos = self._get_pos(edge.coord, edge.direction)

        assert pos >= 0
        
        return bool(self._get_bit(pos))


    def copy(self) -> Self:
        new                     = super().copy()

        new._connections        = self._connections

        new.num_conn_per_row    = self.num_conn_per_row
        new.num_connections     = self.num_connections

        new.board_mask          = self.board_mask
        new.neighbor_mask       = self.neighbor_mask

        return new


    def separated_region(self, start: CoordLike, end: CoordLike) -> frozenset[Coord]:
        ...


    def _get_pos(self, coord: CoordLike, direction: Direction = Direction.NORTH):
        coord       = Coord(*coord)
        # Relative to North
        pos         = coord.x * 2 + coord.y * self.num_conn_per_row

        match direction:
            case Direction.NORTH:
                pass

            case Direction.WEST:
                pos -= 1
                
            case Direction.EAST:
                pos += 1
                
            case Direction.SOUTH:
                pos -= self.num_conn_per_row

        return pos
    


    def _get_bit(self, pos: int):
        return (self._connections >> pos) & 1

    def _flip_bits(self, bits: int):
        return bits ^ self.board_mask


    def parse_bits(self, bits: int, pad: bool = True):
        if pad:
            return f"{bits:0{self.num_connections}b}"[::-1]

        return f"{bits:b}"[::-1]