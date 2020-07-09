from django.urls import path
from . import views

urlpatterns = [
    path("", views.menu, name="napoleon-menu"),
    path("game/", views.game, name="napoleon-game")
]