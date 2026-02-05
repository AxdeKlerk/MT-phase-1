from django.urls import path
from .views import date_page

urlpatterns = [
    path("<slug:venue_slug>/<int:year>-<int:month>-<int:day>/", date_page, name="date_page",),
]
