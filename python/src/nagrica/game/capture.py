from dataclasses    import dataclass

from nagrica.grid   import Coord


@dataclass(frozen=True)
class Capture:
    coords: frozenset[Coord]

    @property
    def points(self):
        return len(self.coords)

    @property
    def split(self):
        # Checks whether there is a new split (A new capture has taken place)
        return self.points > 0
