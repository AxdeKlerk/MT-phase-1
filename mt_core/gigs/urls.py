from django.urls import path
from .views import date_page, payment_page, tip_page, venue

app_name = "gigs"

urlpatterns = [
    path("<slug:venue_slug>/", venue, name="venue"),
    path("tip/<int:gig_id>/", tip_page, name="tip_page",),
    path("<slug:venue_slug>/<int:year>/<int:month>/<int:day>/", date_page, name="date_page"),
    path("payment/<int:gig_id>/<int:amount>/", payment_page, name="payment_page"),
]
