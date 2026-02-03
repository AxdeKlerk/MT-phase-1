from django.urls import path
from gigs.views import date_page_debug

urlpatterns = [
    path('debug/<slug:venue_slug>/<str:gig_date>/', date_page_debug, name='date_page_debug'),
]
