from django.contrib import admin
from django.urls import include, path
from core.views import home
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # path("", home, name="home"), for pahse 2
    path('gigs/', include('gigs.urls')),
    path("", home),
]
