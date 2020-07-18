import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .napoleon import Game, Grid

class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.game_inst = self.scope['url_route']['kwargs']['game_inst']
        self.game_group_name = 'chat_%s' % self.game_inst

        print(self.channel_layer)

        self.game = None
        # Join room group
        await self.channel_layer.group_add(
            self.game_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        player = data["player"]

        if self.game == None:
            grid = Grid(width=data["width"], height=data["height"])
            self.game = Game(grid=grid)
            self.game.add_player(player)
            return
        
        wall_id = data['wall']
        wall_list = wall_id.split("-")
        coord, direction = (int(wall_list[0]), int(wall_list[1])), wall_list[2]
        result = self.game.play(coord, direction, player)

        remove_walls = None

        if result == None:
            tiles = None
        else:
            if result["score"] == None:
                #this means that the last 2 tiles were captured (you can get these by calling "tiles" and "tiles2")
                pass
            tiles = [f"{tile.x}-{tile.y}" for tile in result["tiles"]]
            remove_walls = []
            for tile in result["tiles"]:
                for direction in ["s", "e"]:
                    wall = tile.walls[direction]
                    if not isinstance(wall, napoleon.Border):
                        remove_walls.append(f"{tile.x}-{tile.y}-{direction}")

        move = {
            'player': player,
            'tiles' : tiles,
            'wall' : wall_id,
            'remove_walls' : remove_walls
        }

        # Send message to room group
        await self.channel_layer.group_send(
            self.game_group_name,
            {
                'type': 'make_move',
                'move': move
            }
        )

        # self.send(text_data=json.dumps())

    # Receive message from room group
    async def make_move(self, event):
        move = event['move']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(move))