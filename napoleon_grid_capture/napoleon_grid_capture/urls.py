from django.conf.urls import include
from django.urls import path
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('menu.urls')),
    path('game/', include('game.urls'))
]

urlpatterns += staticfiles_urlpatterns()