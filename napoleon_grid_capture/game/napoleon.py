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
        tiles = [tile1, tile2]


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

    def add_wall(self, coord1, direction):
        """adds a wall to the tile object if it doesn't have one yet"""

        if not self.is_valid_position(coord1):
            print("Address 1 is invalid:", coord1)
            return

        variation = variation_direction[direction]

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

    def make_move(self, coord, direction):
        """takes in address and direction, adds a wall there and checks whether that wall cut off any square"""
        wall_placed_successfully = self.add_wall(coord, direction)

        if wall_placed_successfully:
            self.flood_fill(coord)

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
                captured_tiles[0].out_of_game = 1
                non_captured_tiles[0].out_of_game = 1

                return {
                    "tiles" : captured_tiles,
                    "score" : None,
                    "tiles2" : non_captured_tiles
                }

            for tile in self.get_all_tiles():
                tile.captured = False

            # We make sure that the amount of captured tiles isn't the same as the amount left in the game, since
            if captured_len != self.tiles_left:
                score = min(captured_len, non_captured_len)

                # we only take away the smaller group of tiles
                if captured_len > non_captured_len:
                    for tile in non_captured_tiles:
                        tile.out_of_game = 1
                    final_captured_tiles = non_captured_tiles

                else:
                    for tile in captured_tiles:
                        tile.out_of_game = 1
                    final_captured_tiles = captured_tiles



                self.tiles_left -= score


                return {
                    "tiles" : final_captured_tiles,
                    "score" : score
                }
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

    def flood_fill(self, addr):
        tile = self.get_tile(addr)
        tile.captured = True

        def direction_has_wall(direction):
            return isinstance(tile.walls[direction], Border)
            

        def getSurroundingCoords(x, y):
            return (x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)


        def is_valid_tile(direction, next_tile):
            # print(f"{(tile.x, tile.y)} --{direction}-> {next_tile}")

            next_tile = self.get_tile(next_tile)

            has_wall = direction_has_wall(direction)
            return not has_wall and self.is_valid_position((next_tile.x, next_tile.y)) and not next_tile.captured and not next_tile.out_of_game

        self.counter = 0
        x, y = addr

        n, e, s, w = getSurroundingCoords(x, y)
        
        for direction, coord in zip("nesw", (n, e, s, w)):
            if is_valid_tile(direction, coord):
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
    def __init__(self, grid=None):
        """takes an optional grid instance (in case one doesn't wannt 8x8)"""
        self.players = []
        if grid == None:
            grid = Grid()
        self.grid = grid
        self.counter = 0
        self.numberOfPlayers = 0
        self.moves = []

    def add_player(self, username):
        self.numberOfPlayers += 1

        self.players.append(Player(username, self.grid, self.numberOfPlayers))

    def next_player(self):
        return self.players[(self.counter + 1) % len(self.players)]
        

    def play(self, data):
        self.moves.append(data)

        player = data["player"]
        wall_list = data['wall'].split("-")
        coord, direction = (int(wall_list[0]), int(wall_list[1])), wall_list[2]

        self.numberOfPlayers = len(self.players)
        
        player_rotation = self.counter % self.numberOfPlayers
        current_player = self.players[player_rotation]

        if current_player.username == player:
            result = self.grid.make_move(coord, direction)

            if result != None:
                if (score := result["score"]) == None:
                    current_player.points += 1

                    next_player = self.next_player()
                    next_player.points += 1

                    return result

                current_player.points += score
                self.counter += 1
                return result
        else:
            print("It's not this player's turn")


class Player:
    def __init__(self, username, grid, number):
        self.username = username
        self.grid = grid
        self.points = 0
        self.number = number