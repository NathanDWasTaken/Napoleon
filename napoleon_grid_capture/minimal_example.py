from timeit import timeit
from random import randint

class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Grid:
    def __init__(self, size):
        self.tiles_list = []
        for y in range(size):
            row = []
            for x in range(size):
                row.append(Tile(x, y))
            self.tiles_list.append(row)

        self.tiles_dict = {}
        for y in range(size):
            for x in range(size):
                self.tiles_dict[(x, y)] = Tile(x, y)
        
my_setup = """
from random import randint

class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Grid:
    def __init__(self, size):
        self.tiles_list = []
        for y in range(size):
            row = []
            for x in range(size):
                row.append(Tile(x, y))
            self.tiles_list.append(row)

        self.tiles_dict = {}
        for y in range(size):
            for x in range(size):
                self.tiles_dict[(x, y)] = Tile(x, y)

size = 8
grid = Grid(size)
"""

list_code = "tile = grid.tiles_list[randint(0, size - 1)][randint(0, size - 1)]"
dict_code = "tile = grid.tiles_dict[randint(0, size - 1), randint(0, size - 1)]"


print(timeit(setup = my_setup, stmt = list_code, number = 10000000))
print(timeit(setup = my_setup, stmt = dict_code, number = 10000000))