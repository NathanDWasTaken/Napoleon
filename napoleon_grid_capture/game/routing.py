from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/game/local/(?P<game_id>\w+)/$', consumers.LocalConsumer),
    re_path(r'ws/game/(?P<game_id>\w+)/$', consumers.MultiplayerConsumer),
]