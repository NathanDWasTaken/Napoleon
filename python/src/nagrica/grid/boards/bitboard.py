from typing         import Self
from enum           import IntEnum

from .board         import Board

from nagrica.grid.direction     import Direction 
from nagrica.grid.coord         import Coord, CoordLike
from nagrica.grid.edge          import Edge


class Axis(IntEnum):
    VER = 0
    HOR = 1


class BitBoard(Board):

    # Bitmask for connected cells
    # VER: Based on North
    # HOR: Based on East
    connections:    dict[Axis, int]
    board_mask:     int

    num_tiles:      int


    def build_board(self, height: int, width: int):
        self.num_tiles      = height * width
        self.board_mask     = (1 << self.num_tiles) -1

        self.connections    = {}
        self.connections[Axis.VER]  = int("1" * max(1, height - 1) * width, base=2)
        self.connections[Axis.HOR]  = int(("0" + "1" * (width - 1)) * height, base=2)



    # Do and Undo actions

    def place_wall(self, wall: Edge):
        """
        Assumes GameState has validated edge
        """

        axis, pos = self._calc_bitpos(wall.coord, wall.direction)

        self.connections[axis] &= self.board_mask - (2 ** pos)



    def remove_wall(self, wall: Edge):
        """
        Assumes GameState has validated edge
        """

        axis, pos = self._calc_bitpos(wall.coord, wall.direction)

        self.connections[axis] |= 2 ** pos


    # Helper functions

    def connects(self, edge: Edge) -> bool:
        if not self.edge_is_valid(edge):
            return False

        axis, pos = self._calc_bitpos(edge.coord, edge.direction)
        
        return bool(self._get_bitpos(axis, pos))


    def copy(self) -> Self:
        new                 = super().copy()

        new.connections     = self.connections.copy()
        new.board_mask      = self.board_mask
        new.num_tiles       = self.num_tiles

        return new


    def _wall_is_connected(self, coord1: Coord, coord2: Coord) -> bool:
        """
        Checks whether the wall to be connected has adjacent walls on both sides.
        In practice this does not save any time (and actually costs time), 
        since the cases where there is no adjacent wall are the same cases where floodfill can reach in few iterations
        """

        pos1    = self._calc_axis_pos(coord1)
        pos2    = self._calc_axis_pos(coord2)

        walls_n = self.board_mask ^ self.connections[Axis.VER]
        walls_e = self.board_mask ^ self.connections[Axis.HOR]

        direction = coord1.direction_to(coord2)

        match direction:
            case (Direction.NORTH | Direction.SOUTH):
                bot_pos = pos1 if direction == Direction.NORTH else pos2

                left = bool(
                       (coord1.x == 0 and coord2.x == 0)    # On the border
                    or (walls_e >> (pos1 - 1   ))   & 1     # left, down
                    or (walls_e >> (pos2 - 1   ))   & 1     # left, up
                    or (walls_n >> (bot_pos - 1))   & 1     # left, left
                )

                right = bool(
                       (coord1.x == self.width - 1 or coord2.x == self.width - 1)
                    or (walls_e >> (pos1))          & 1     # right down (assuming pos1 is bottom)
                    or (walls_e >> (pos2))          & 1     # right, up
                    or (walls_n >> (bot_pos + 1))   & 1     # right, right
                )

                return left and right

            case (Direction.EAST | Direction.WEST):
                left_pos    = pos1 if direction == Direction.EAST else pos2

                up = bool(
                       (coord1.y == self.height - 1 and coord2.y == self.height - 1)
                    or (walls_n >> (pos1))                  & 1     # up, left
                    or (walls_n >> (pos2))                  & 1     # up, right
                    or (walls_e >> (left_pos + self.width)) & 1     # up, up
                )

                down = bool(
                       (coord1.y == 0 and coord2.y == 0)
                    or (walls_n >> (pos1 - self.width))     & 1     # down, left
                    or (walls_n >> (pos2 - self.width))     & 1     # down, right
                    or (walls_e >> (left_pos - self.width)) & 1     # down, down
                )

                return up and down


    def separated_region(self, start: Coord, end: Coord) -> frozenset[Coord]:
        # if not self._wall_is_connected(start, end):
        #     return frozenset()

        # MITM seperated region

        frontiers = [
            1 << self._calc_axis_pos(start),
            1 << self._calc_axis_pos(end)
        ]

        c = 0

        while True:
            i               = c % 2
            frontier_old    = frontiers[i]

            # shift north
            frontiers[i] |= self.board_mask & ((self.connections[Axis.VER] & frontiers[i]) << self.width)
            # shift east
            frontiers[i] |= self.board_mask & ((self.connections[Axis.HOR] & frontiers[i]) << 1)
            # shift west
            frontiers[i] |= self.board_mask & (((self.connections[Axis.HOR] << 1) & frontiers[i]) >> 1)
            # shift south
            frontiers[i] |= self.board_mask & (((self.connections[Axis.VER] << self.width) & frontiers[i]) >> self.width)

            # If we reach goal, no seperated region
            if frontiers[0] & frontiers[1]:
                return frozenset()

            # If value is no longer updated and we have not reached the goal, then the region is seperated
            if frontiers[i] == frontier_old:
                break

            c += 1

        # Convert Bitmask of visited tiles back to Coords
        visited_coords = self._coords_from_set_bits(frontiers[i])

        return frozenset(visited_coords)

        

    def _coords_from_set_bits(self, bits: int) -> set[Coord]:
        coords      = set()

        while True:
            low     = bits & -bits
            index   = low.bit_length() - 1
            coord   = self._coords[index // self.width][index %  self.width]

            coords.add(coord)

            bits   ^= low

            if bits == 0:
                break


        return coords



    def _calc_bitpos(self, coord: CoordLike, direction: Direction) -> tuple[Axis, int]:
        pos = self._calc_axis_pos(coord)

        match direction:
            case Direction.NORTH:
                return Axis.VER, pos
                
            case Direction.EAST:
                return Axis.HOR, pos

            case Direction.WEST:
                return Axis.HOR, pos - 1
                
            case Direction.SOUTH:
                return Axis.VER, pos - self.width
    
    def _calc_axis_pos(self, coord: CoordLike) -> int:
        return coord[0] + coord[1] * self.width

    def _get_bitpos(self, axis: Axis, pos: int):
        return (self.connections[axis] >> pos) & 1


    def _flip_bits(self, bits: int):
        return bits ^ self.board_mask

