from typing     import NamedTuple
from math       import sqrt


class Vector[T: (int, float)](NamedTuple):
    dx: T
    dy: T


    @property
    def opposite(self):
        return self.__class__(-self.dx, -self.dy)

    @property
    def length(self) -> float:
        return sqrt(self.dx ** 2 + self.dy ** 2)


    def dot(self, other: Vector[T]) -> float:
        return self.dx * other.dx + self.dy * other.dy


    def similarity(self, other: Vector[T]) -> float:
        return self.dot(other) / (self.length * other.length)


    def __truediv__(self, other: float) -> Vector[float]:
        return Vector(
            self.dx / other,
            self.dy / other
        )

    def __abs__(self) -> Vector[T]:
        return Vector(
            max(self.dx, -self.dx),
            max(self.dy, -self.dy)
        )