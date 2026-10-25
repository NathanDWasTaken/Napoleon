from .capture       import Capture, CaptureEvaluation

from nagrica.grid   import Board, Coord, CoordLike



class GreedyDFS(CaptureEvaluation):
    board: Board
    
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
            if not self.board.connects(point, direction):
                continue

            next = point.to_neighbor(direction)

            if next in self.visited:
                continue
            
            result = self._traverse(next)

            if result:
                return True

        return False


    def run(self, start: CoordLike, end: CoordLike) -> Capture:
        start, end                  = Coord(*start), Coord(*end)
        self.visited: set[Coord]    = set()
        self._goal                  = end

        result = self._traverse(start)

        if result:
            return Capture(frozenset())


        if len(self.visited) > self.board.num_in_play / 2:
            captured    = set(self.board.in_play) - self.visited
        else:
            captured    = self.visited

        return Capture(frozenset(captured))
