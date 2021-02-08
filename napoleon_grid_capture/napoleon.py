# pos is a coordinate in the form (x, y)


def subtract_2_addresses(coord1, coord2, operation="-"):
    """do operation element wise between coord1 and coord2"""
    difference = []

    for element2, element1 in zip(coord2, coord1):
        if operation == "-":
            result = element2 - element1
        elif operation == "+":
            result = element2 + element1

        difference.append(result)

    return tuple(difference)

# returns either:
# - the variation of coordinate when going a certain direction
# - the direction for a certain variation in coords

# east -> x + 1 | x + 1 -> east
variation_direction = {
    "n": (0, -1), (0, -1): "n", 
    "e": (1, 0), (1, 0): "e", 
    "s": (0, 1), (0, 1): "s", 
    "w": (-1, 0), (-1, 0): "w"}
    
opposite_direction = {"n" : "s", "e" : "w", "s" : "n", "w" : "e"}

class Tile:
    def __init__(self, x, y):
        self.value = 0
        self.x = x
        self.y = y
        self.out_of_game = False

        self.captured  = False
        
        self.walls = {"n" : None, "e" : None, "s" : None, "w" : None}


class Border:
    pass


class Wall(Border):
    def __init__(self, tile1, tile2):
        self.tiles = [tile1, tile2]


class Grid:
    def __init__(self, width=8, height=8):
        if 1 < width and 1 < height:
            self.width, self.height = width, height
            self.total_tiles = width * height
            self.tiles_left = self.total_tiles
            self.grid = []

            for y in range(height):
                row = []
                for x in range(width):
                    tile = Tile(x, y)

                    if y == 0:
                        tile.walls["n"] = Border()
                    if x == width - 1:
                        tile.walls["e"] = Border()
                    if y == height - 1:
                        tile.walls["s"] = Border()
                    if x == 0:
                        tile.walls["w"] = Border()

                    row.append(tile)
                self.grid.append(row)
        else:
            print("Both grid dimensions have to be bigger than 1")

    def add_wall(self, coord1, direction = None, coord2 = None):
        """adds a wall to the tile object if it doesn't have one yet"""

        if not self.is_valid_position(coord1):
            print("Address 1 is invalid:", coord1)
            return

        if coord2 != None:
            if not self.is_valid_position(coord2):
                print("Address 2 is invalid:", coord2)
                return

            # we need to figure out direction when going from addr1 to addr2
            pos_variation = subtract_2_addresses(coord1, coord2)
            direction = variation_direction[pos_variation]


        if direction != None:
            variation = variation_direction[direction]

            if coord2 == None:
                # we can figure out coords of addr2 if we know addr1 and the direction it wants to go
                coord2 = subtract_2_addresses(coord1, variation, operation="+")
                if not self.is_valid_position(coord2):
                    print("Address 2 is not Valid")
                    return

            tile1 = self.get_tile(coord1)
            tile2 = self.get_tile(coord2)

            wall = Wall(tile1, tile2)
            if not isinstance(tile1.walls[direction], Wall):
                tile1.walls[direction] = wall
            
            if not isinstance(tile2.walls[opposite_direction[direction]], Wall):
                tile2.walls[opposite_direction[direction]] = wall

            return True

    def make_move(self, coord1, coord2=None, direction=None, player_number=1):
        """takes in address and direction, adds a wall there and checks whether that wall cut off any square"""
        wall_placed_successfully = self.add_wall(coord1, coord2 = coord2, direction = direction)

        if wall_placed_successfully:
            self.flood_fill(coord1)

            non_captured_tiles = []
            captured_tiles = []

            score = 0

            for tile in self.get_all_tiles():
                if not tile.out_of_game:
                    if tile.captured == True:
                        captured_tiles.append(tile)
                    else:
                        non_captured_tiles.append(tile)
            
            captured_len = len(captured_tiles)
            non_captured_len = len(non_captured_tiles)

            if captured_len == non_captured_len == 1:
                captured_tiles[0].out_of_game = player_number
                return non_captured_tiles[0]

            # We make sure that the amount of captured tiles isn't the same as the amount left in the game, since
            if captured_len != self.tiles_left:
                score = min(captured_len, non_captured_len)

                # we only take away the smaller group of tiles
                if captured_len > non_captured_len:
                    for tile in non_captured_tiles:
                        tile.out_of_game = player_number

                else:
                    for tile in captured_tiles:
                        tile.out_of_game = player_number

            for tile in self.get_all_tiles():
                tile.captured = False

            self.tiles_left -= score

            self.print_board() 

            return score
        else:
            print("Could not add wall")
            return None




    def is_valid_position(self, addr):
        """returns whether the given address is in the grid bounds"""
        if addr != None:
            return 0 <= addr[0] <= self.width - 1 and 0 <= addr[1] <= self.height - 1


    def get_tile(self, pos):
        """returns the tile object for a given address, if the address is valid"""
        x, y = pos
        if self.is_valid_position(pos):
            return self.grid[y][x]
        
    def get_all_tiles(self):
        for row in self.grid:
            for tile in row:
                yield tile

    def direction_has_wall(self, tile, direction):
        return isinstance(tile.walls[direction], Border)
            

    def getSurroundingCoords(self, x, y):
        return (x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)


    def is_valid_tile(self, current_tile, direction, next_tile):
        # print(f"{(tile.x, tile.y)} --{direction}-> {next_tile}")

        next_tile = self.get_tile(next_tile)

        has_wall = self.direction_has_wall(current_tile, direction)
        return not has_wall and self.is_valid_position((next_tile.x, next_tile.y)) and not next_tile.captured and not next_tile.out_of_game

    def flood_fill(self, addr):
        tile = self.get_tile(addr)
        tile.captured = True

        self.counter = 0
        x, y = addr

        n, e, s, w = self.getSurroundingCoords(x, y)
        
        for direction, coord in zip("nesw", (n, e, s, w)):
            if self.is_valid_tile(tile, direction, coord):
                self.flood_fill(coord)
        


    def print_board(self):
        def print_horizontal(row, bottom=False):
            print_row = ""
            for tile in row:
                tile_n = tile.walls["n"]
                if tile_n != None or bottom:
                    print_row += " ———"
                else:
                    print_row += "    "
            print(print_row)
            
        def print_vertical(row):
            print_row = "|"
            for tile in row:
                if tile.out_of_game:
                    captured = tile.out_of_game
                else:
                    captured = 0
                
                tile_e = tile.walls["e"]
                if tile_e != None:
                    print_row += f" {captured} |"
                else:
                    print_row += f" {captured}  "
            print(print_row)

        for row in self.grid:
            print_horizontal(row)
            print_vertical(row)
        print_horizontal(self.grid[-1], bottom=True)


class Game:
    def __init__(self, grid=None, coord_system="normal"):
        """takes an optional grid instance (in case one doesn't wannt 8x8) and the coordinate system, normal or programming.
            top left tile's coords:
                'normal': (1, 1)
                'programming': (0, 0)
                """
        self.players = []
        if grid == None:
            grid = Grid()
        self.grid = grid
        self.counter = 0
        self.coord_system = coord_system
        self.over = False

    def add_player(self, username):
        player_number = len(self.players) + 1

        self.players.append(Player(username, self.grid, player_number))

    def next_player(self):
        return self.players[(self.counter + 1) % len(self.players)]

    def input_to_coords(self, name, number):
        entry = input(f"{name} ({number}): ")

        data = entry.split()
        try:
            # We get the x, y coordinates as well as the direction d
            x, y, d = data
            x, y = int(x), self.grid.height - int(y)


            if self.coord_system == "normal":
                return (x - 1, y), d

            elif self.coord_system == "programming":
                return (x, y - 1), d
                
        except ValueError:
            print(f"The input is invalid: {entry}")
            return self.input_to_coords(name, number)
        

    def play(self):
        player_number = len(self.players)
        
        print("Here is the current board:")
        self.grid.print_board()

        print("Give an input in the following format: 'x y direction'. x and y are coordinates, direction is either n/e/s/w")
        while True:
            player_rotation = self.counter % player_number
            current_player = self.players[player_rotation]

            addr, direction = self.input_to_coords(current_player.username, current_player.number)

            if direction in ["n", "e", "s", "w"]:
                score = self.grid.make_move(addr, direction = direction, player_number = current_player.number)
                # if a tile is returned, that means that it's the end of the game
                if isinstance(score, Tile):
                    last_tile = score
                    self.over = True

                    current_player.points += 1

                    next_player = self.next_player()
                    next_player.points += 1
                    last_tile.out_of_game = next_player.number

                    self.grid.print_board()
                    print("Scores:")
                    for player in self.players:
                        print(f"- {player.username} ({current_player.number}): {player.points}")
                    break
                elif score != None:
                    current_player.points += score
                    self.counter += 1
                elif score == None:
                    print("Invalid wall, try again.")


class Player:
    def __init__(self, username, grid, number):
        self.username = username
        self.grid = grid
        self.points = 0
        self.number = number


# def minmax(position, depth=4, alpha=float("-inf"), beta=float("inf"), maximizingPlayer):
#     if depth == 0 or 

def Max_n(position, player, upper_bound, depth=3):
    if depth == 0 or position.over:
        return position.

if __name__ == "__main__":
    game = Game(Grid(4, 4))

    game.add_player("Player 1")

    game.add_player("Player 2")

    game.play()