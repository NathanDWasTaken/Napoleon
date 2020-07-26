from django.urls import path
from . import views as menu_views
from game import views as game_views

urlpatterns = [
    path("", menu_views.menu, name="napoleon-menu"),
    path("local/", game_views.local_redirect, name="napoleon-local")
]