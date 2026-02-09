from django.urls import path
from .views import date_page, tip_page, venue, start_payment

app_name = "gigs"

urlpatterns = [
    path("<slug:venue_slug>/", venue, name="venue"),
    path("tip/<int:gig_id>/", tip_page, name="tip_page",),
    path("<slug:venue_slug>/<int:year>/<int:month>/<int:day>/", date_page, name="date_page"),
    path("start_payment/", start_payment, name="start_payment"),
]
