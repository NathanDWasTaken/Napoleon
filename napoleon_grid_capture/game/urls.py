from django.urls import path
from . import views

urlpatterns = [
    path("", views.game_selection, name="game-selection"),
    path("<str:game_id>/", views.game, name="napoleon-game")
]