from project_classes import Grid, Players



g = Grid(width = 4, height = 4)

players = Players(grid = g)

players.add_player("Alice")
players.add_player("Bob")

players.play()