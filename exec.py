from project_classes import Grid, Players
from ast import literal_eval



g = Grid(width = 4, height = 4)

players = Players(grid = g)

players.add_player("red", "Player")
players.add_player("blue", "Player")

players.play()