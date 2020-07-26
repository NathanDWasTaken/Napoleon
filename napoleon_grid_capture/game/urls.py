from django.urls import path
from . import views

urlpatterns = [
    path("", views.game_selection, name="game-selection"),
    path("local/", views.local_redirect, name="napoleon-local"),
    path("local/<str:game_id>/", views.local, name="napoleon-local-game"),
    path("<str:game_id>/", views.multiplayer, name="napoleon-multiplayer-game")
]