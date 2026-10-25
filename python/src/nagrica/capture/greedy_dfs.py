from logging        import getLogger

from .capture                    import Capture, CaptureEvaluation
from nagrica.grid.coord          import Coord, CoordLike
from nagrica.grid.board          import Board
from nagrica.grid.direction      import Direction
from nagrica.grid.render         import render_board


logger = getLogger(__file__)



class GreedyDFS(CaptureEvaluation):
    board: Board

    def __init__(self, board: Board) -> None:
        self.board = board

    
    def _traverse(
        self,
        point:          Coord
    ):
        self.visited.add(point)
        
        if point == self._goal:
            return True
        
        offset      = point.offset_to(self._goal)
        directions  = self._direction_order(offset)
        
        for direction in directions:
            cell = self.board[point]

            if not cell.connects(direction):
                continue

            next = point.to_neighbor(direction)

            if next in self.visited:
                continue

            logger.debug("\n" + render_board(self.board, {c: "·" if c != point else direction.name[0] for c in self.visited}))
            
            result = self._traverse(next)

            if result:
                return True

        return False


    def run(self, start: CoordLike, end: CoordLike) -> Capture:
        start, end                  = Coord(*start), Coord(*end)
        self.visited: set[Coord]    = set()
        self._goal                  = end

        result = self._traverse(start)

        logger.debug("\n" + render_board(self.board, {c: "·" if c != self._goal else "X" for c in self.visited}))

        if result:
            return Capture(frozenset())


        if len(self.visited) > len(self.board.in_play) / 2:
            captured    = self.board.in_play - self.visited
        else:
            captured    = self.visited

        return Capture(frozenset(captured))



if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)


    b   = Board(4, 4)
    ce  = GreedyDFS(b)


    from random import randint, choice


    i = 0
    n = randint(5, 15)
    while i < n:
        coord = Coord(
            randint(0, b.width  - 1),
            randint(0, b.height - 1)
        )
        direction   = choice(list(Direction))
        other       = coord.to_neighbor(direction)

        if not (b.coord_is_valid(other) and b.neighbor_is_reachable(coord, direction)):
            continue

        print("-----------------------------------------")
        print(f"Placing {coord} {direction.name}")
        print("-----------------------------------------")

        b.place_wall(coord, direction)

        result  = ce.run(coord, other)

        i += 1


    ...