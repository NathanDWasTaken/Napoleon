import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .napoleon import Game, Grid, Border

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['game_id']

        # Join room group
        await self.channel_layer.group_add(
            self.game_id,
            self.channel_name
        )
        self.lobby_leader = False

        default_group = {"game_inst" : None, "consumers" : {} , "started" : False}

        try:
            self.group = self.get_group()
        except AttributeError:
            self.channel_layer.game_groups = {self.game_id : default_group}
        except KeyError:
            self.channel_layer.game_groups[self.game_id] = default_group
        self.group = self.get_group()

        self.score = 0

        await self.accept()

    
    def get_group(self):
        return self.channel_layer.game_groups[self.game_id]

    
    # Send message to member in group
    async def send_packet(self, event):
        packet = event['packet']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(packet))


















class MultiplayerConsumer(GameConsumer):
    async def disconnect(self, close_code):
        # Let consumers know one user disconnected
        await self.channel_layer.group_send(
            self.game_id, 
            {
                'type' : 'send_packet',
                'packet' : {
                    'command' : 'disconnect player',
                    'player' : self.username
                }
            }
        )

        self.consumers.pop(self.username)

        if self.consumers == {}:
            self.channel_layer.game_groups.pop(self.game_id)
        else:
            # Remove player from game instance
            self.game_inst.remove_player(self.username)


            next_player_name = self.game_inst.current_player.username
            next_player = self.consumers[next_player_name]

            # If only one player left, make remaining player winner
            if len(self.game_inst.players) == 1:
                winner = self.game_inst.players[0]
                await next_player.send(text_data=json.dumps({
                    "command" : "last player",
                    "results" : [(winner.username, winner.points)]
                }))
            else:
                await next_player.send(text_data=json.dumps({"command" : "my turn"}))

        # Leave room group
        await self.channel_layer.group_discard(
            self.game_id,
            self.channel_name
        )

        if self.channel_layer.game_groups == {}:
            delattr(self.channel_layer, "game_groups")

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.pop("command")


        if command == "join":
            self.group = self.get_group()
            self.username = data["player"]
            self.colour = data["colour"]

            if not self.group["started"]:
                if (game_inst := self.group["game_inst"]) == None:
                    grid = Grid(width=data["width"], height=data["height"])
                    game = Game(grid=grid)
                    game.add_player(self.username, self.colour)
                    self.group["game_inst"] = game
                    
                    self.lobby_leader = True
                else:
                    game_inst.add_player(self.username, self.colour)
            else:
                print(f"Game has already started, adding {self.username} to spectators")

            self.consumers = self.group["consumers"]
            self.consumers[self.username] = self

            self.game_inst = self.group["game_inst"]
            self.players = self.game_inst.players

            for move in self.game_inst.moves:
                await self.send(text_data=json.dumps(move))

            await self.send(text_data=json.dumps({
                "command" : "join response",
                "lobby leader" : self.lobby_leader
            }))


            add_player = {
                "command" : "add player",
                "players" : [{"username" : self.username, "colour" : self.colour}]
            }

            await self.channel_layer.group_send(
                self.game_id,
                {
                    'type': 'send_packet',
                    'packet': add_player
                }
            )

            players = []

            for username in self.consumers:
                player = self.consumers[username]
                if player != self:
                    players.append({"username" : player.username, "colour" : player.colour})

            await self.send(text_data=json.dumps({
                "command" : "add player",
                "players" : players
            }))
        elif command == "make move":
            remove_walls = None

            result = self.game_inst.play(data)
            next_player = self.game_inst.current_player

            if result == "InvalidTurn":
                return

            elif result == None:
                tiles = None

            elif result["outcome"] == "end":
                #this means that the last 2 tiles were captured (you can get these by calling "tiles" and "tiles2")
                
                tile1 = result["tiles"][0]
                tile1_id = f"{tile1.x}-{tile1.y}"
                player_inst = self.game_inst.current_player

                move1 = {
                    'command' : "add move",
                    'score' : player_inst.points,
                    'player' : self.username,
                    'colour' : self.colour,
                    'tiles' : [tile1_id],
                    'wall' : data['wall'],
                    'remove_walls' : [data["wall"]]
                }

                # Since there is now only a single tile left the last move is done automatically without the player

                tile2 = result["tiles2"][0]
                tile2_id = f"{tile2.x}-{tile2.y}"

                player2_inst = self.game_inst.next_player()

                move2 = {
                    'command' : "add move",
                    'score' : player2_inst.points,
                    'player' : next_player.username,
                    'colour' : self.consumers[player2_inst.username].colour,
                    'tiles' : [tile2_id],
                    'wall' : None,
                    'remove_walls' : None
                }

                sorted_results = list(sorted(self.players, key = lambda x: x.points, reverse=True))

                end_packet = {
                    'command' : 'end',
                    'results' : [(player.username, player.points) for player in sorted_results]
                }

                for packet in [move1, move2, end_packet]:
                    await self.channel_layer.group_send(
                        self.game_id,
                        {
                            'type': 'send_packet',
                            'packet': packet
                        }
                    )

                return 
    
            else:
                self.score = result["total score"]
                tiles = [f"{tile.x}-{tile.y}" for tile in result["tiles"]]
                remove_walls = []
                for tile in result["tiles"]:
                    for direction in ["s", "e"]:
                        wall = tile.walls[direction]
                        if not isinstance(wall, Border):
                            remove_walls.append(f"{tile.x}-{tile.y}-{direction}")

            move = {
                'command' : "add move",
                'score' : self.score,
                'player': self.username,
                'colour' : self.colour,
                'tiles' : tiles,
                'wall' : data['wall'],
                'remove_walls' : remove_walls,
                'next player' : next_player.username
            }

            self.game_inst.moves.append(move)

            # Send message to room group
            await self.channel_layer.group_send(
                self.game_id,
                {
                    'type': 'send_packet',
                    'packet': move
                }
            )


        elif command == "start":
            if self.lobby_leader:
                await self.send(text_data=json.dumps({
                    "command" : "start response",
                    "player turn" : True
                    }))
                self.group["started"] = True
            else:
                print(f"Sorry but {self.username} can't start the game")

        else:
            print(command)












































class LocalConsumer(GameConsumer):
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.game_id,
            self.channel_name
        )

        self.channel_layer.game_groups.pop(self.game_id)

        if self.channel_layer.game_groups == {}:
            delattr(self.channel_layer, "game_groups")

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.pop("command")

        if command == "join":
            self.group = self.get_group()

            # if game inst already exists
            if (game_inst := self.group["game_inst"]) != None:
                for move in game_inst.moves:
                    await self.send(text_data=json.dumps(move))
            
            # if game hasn't started
            elif not self.group["started"]:
                grid = Grid(width=data["width"], height=data["height"])
                game_inst = Game(grid=grid)
                self.group["game_inst"] = game_inst

            self.players = []
            for player in data["players"]:
                player = game_inst.add_player(player["username"], player["colour"])
                self.players.append(player)

        elif command == "make move":
            remove_walls = None

            game_inst = self.group["game_inst"]

            result = game_inst.play(data)


            player_name = data["player"]
            player_inst = game_inst.players_dict[player_name]

            if result == "InvalidTurn":
                return
            elif result == None:
                tiles = None
            else:
                if result["outcome"] == "end":
                    #this means that the last 2 tiles were captured (you can get these by calling "tiles" and "tiles2")

                    tile1 = result["tiles"][0]
                    tile1_id = f"{tile1.x}-{tile1.y}"

                    move1 = {
                        'command' : 'add move',
                        'score' : player_inst.points,
                        'player' : player_name,
                        'colour' : data["colour"],
                        'tiles' : [tile1_id],
                        'wall' : data['wall'],
                        'remove_walls' : [data["wall"]]
                    }

                    tile2 = result["tiles2"][0]
                    tile2_id = f"{tile2.x}-{tile2.y}"

                    next_player_name = data["next player"]

                    move2 = {
                        'command' : 'add move',
                        'score' : game_inst.players_dict[next_player_name].points,
                        'player' : next_player_name,
                        'colour' : data["next colour"],
                        'tiles' : [tile2_id],
                        'wall' : None,
                        'remove_walls' : None
                    }

                    sorted_results = list(sorted(self.players, key = lambda x: x.points, reverse=True))

                    end_packet = {
                        'command' : 'end',
                        'results' : [(player.username, player.points) for player in sorted_results]
                    }

                    for packet in [move1, move2, end_packet]:
                        await self.send(text_data=json.dumps(packet))

                    return

                else:
                    tiles = [f"{tile.x}-{tile.y}" for tile in result["tiles"]]
                    remove_walls = []
                    for tile in result["tiles"]:
                        for direction in ["s", "e"]:
                            wall = tile.walls[direction]
                            if not isinstance(wall, Border):
                                remove_walls.append(f"{tile.x}-{tile.y}-{direction}")

            move = {
                'command' : 'add move',
                'score' : player_inst.points,
                'player': player_name,
                'colour' : data["colour"],
                'tiles' : tiles,
                'wall' : data['wall'],
                'remove_walls' : remove_walls
            }

            game_inst.moves.append(move)

            # Send message to room group
            await self.send(text_data=json.dumps(move))
