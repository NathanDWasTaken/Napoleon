def subtract_2_addresses(address2, address1, operation = "-"):
    difference = []

    zip_object = zip(address1, address2)
    for list1_i, list2_i in zip_object:
        if operation == "-":
            result = list1_i - list2_i
        elif operation == "+":
            result = list1_i + list2_i

        difference.append(result)

    return tuple(difference)
    
# returns either the variation of coords when going a certain direction, or returns a direction for a certain variation in coords
# east -> x + 1 | x + 1 -> east
variation_direction = {'n': (0, -1), (0, -1): 'n', 'e': (1, 0), (1, 0): 'e', 's': (0, 1), (0, 1): 's', 'w': (-1, 0), (-1, 0): 'w'}
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
    def __init__(self, width = 8, height = 8):
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

    def add_wall(self, address1, direction = None, address2 = None):
        """adds a wall to the tile object if it doesn't have one yet"""
        if not self.is_valid_address(address1):
            print("Address 1 is invalid:", address1)
            return
        elif address2 != None and not self.is_valid_address(address2):
            print("Address 2 is invalid:", address2)
            return

        if direction == None and address2 != None:
            print("direction is None and address2 is not None")
            # we need to figure out direction when going from addr1 to addr2
            variation = subtract_2_addresses(address1, address2)
            direction = variation_direction[variation]

        if direction != None:
            variation = variation_direction[direction]

            if address2 == None:
                # we can figure out coords of addr2 if we know addr1 and the direction it wants to go
                address2 = subtract_2_addresses(address1, variation, operation = "+")
                if not self.is_valid_address(address2):
                    print("Address 2 is not Valid")
                    return

            tile1 = self.get_tile(address1)
            tile2 = self.get_tile(address2)

            if not isinstance(tile1.walls[direction], Wall) or not isinstance(tile2.walls[opposite_direction[direction]], Wall):
                wall = Wall(tile1, tile2)

                tile1.walls[direction] = wall
                tile2.walls[opposite_direction[direction]] = wall

                return True

    def make_move(self, address1, address2 = None, direction = None, player_number = 1):
        """takes in address and direction, adds a wall there and checks whether that wall cut off any square"""
        wall_placed_successfully = self.add_wall(address1, address2 = address2, direction = direction)

        if wall_placed_successfully:
            self.flood_fill(address1)
            non_captured_tiles = []
            captured_tiles = []

            score = 0

            for tile in self.yield_tiles():
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

            if captured_len != self.tiles_left:
                # if tiles captured is more than half, it means that the non_captured_tiles are the least and get taken
                if captured_len > non_captured_len:
                    for tile in non_captured_tiles:
                        tile.captured = True
                        tile.out_of_game = player_number

                    for tile in captured_tiles:
                        tile.captured = False
                    score = non_captured_len
                else:
                    for tile in captured_tiles:
                        tile.out_of_game = player_number
                    score = captured_len

            else:
                for tile in self.yield_tiles():
                    tile.captured = False

            self.tiles_left -= score

            self.print_board() 

            return score
        else:
            print("Could not add wall")
            return None




    def is_valid_address(self, addr):
        """returns whether the given address is in the grid bounds"""
        if addr != None:
            return 0 <= addr[0] <= self.width - 1 and 0 <= addr[1] <= self.height - 1


    def get_tile(self, addr):
        """returns the tile object for a given address, if the address is valid"""
        x, y = addr
        if self.is_valid_address(addr):
            return self.grid[y][x]
        
    def yield_tiles(self, array = None):
        if array == None:
            array = self.grid

        for row in array:
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
            return not has_wall and self.is_valid_address((next_tile.x, next_tile.y)) and not next_tile.captured and not next_tile.out_of_game

        self.counter = 0
        x, y = tile.x, tile.y

        n, e, s, w = getSurroundingCoords(x, y)

        if is_valid_tile("n", n):
            self.flood_fill(n)

        if is_valid_tile("e", e):
            self.flood_fill(e)

        if is_valid_tile("s", s):
            self.flood_fill(s)
            
        if is_valid_tile("w", w):
            self.flood_fill(w)

    def print_board(self):
        def print_horizontal(bottom = False):
            row = ""
            for tile in y:
                tile_n = tile.walls["n"]
                if tile_n != None or bottom:
                    row += " ———"
                else:
                    row += "    "
            print(row)
            
        def print_vertical():
            row = "|"
            for tile in y:
                if tile.out_of_game:
                    captured = tile.out_of_game
                else:
                    captured = 0
                
                tile_e = tile.walls["e"]
                if tile_e != None:
                    row += f" {captured} |"
                else:
                    row += f" {captured}  "
            print(row)

        for y in self.grid:
            print_horizontal()
            print_vertical()
            if y == self.grid[self.height - 1]:
                print_horizontal(bottom = True)


class Players:
    def __init__(self, grid = None, coord_system = "normal"):
        """takes an optional grid instance (in case one doesn't wannt 8x8) and the coordinate system, math or programming. In 'math' the top left tile is 1 1, for 'programming' this is 0 0"""
        self.players = []
        if grid == None:
            grid = Grid()
        self.grid = grid
        self.counter = 0
        self.system = coord_system

    def add_player(self, username):
        player_number = len(self.players) + 1

        self.players.append(Player(username, self.grid, player_number))

    def next_player(self):
        return self.players[(self.counter + 1) % len(self.players)]

    def input_to_coords(self, entry):
        data = entry.split()
        if self.system == "normal":
            return (int(data[0]) - 1, int(data[1]) - 1), data[2]

        elif self.system == "programming":
            return (int(data[0]), int(data[1])), data[2]
        


    def play(self):
        player_number = len(self.players)
        
        print("Here is the current board:")
        self.grid.print_board()

        print("Give an input in the following format: 'x y direction'. x and y are coordinates, direction is either n/e/s/w")
        while True:
            player_rotation = self.counter % player_number
            current_player = self.players[player_rotation]

            addr, direction = self.input_to_coords(input(f"{current_player.username} ({current_player.number}): "))

            if direction in ["n", "e", "s", "w"]:
                score = self.grid.make_move(addr, direction = direction, player_number = current_player.number)
                if isinstance(score, Tile):
                    current_player.points += 1

                    next_player = self.next_player()
                    next_player.points += 1
                    score.out_of_game = next_player.number

                    self.grid.print_board()
                    print("Scores:")
                    for player in self.players:
                        print(f"- {player.username} ({current_player.number}): {player.points}")
                    break
                elif score != None:
                    current_player.points += score
                    self.counter += 1


class Player:
    def __init__(self, username, grid, number):
        self.username = username
        self.grid = grid
        self.points = 0
        self.number = number