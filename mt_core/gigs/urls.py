from django.urls import path
from .views import date_page, tip_page, venue, start_payment, create_payment_intent, phase1_report

app_name = "gigs"

urlpatterns = [
    path("tip/<int:gig_id>/", tip_page, name="tip_page",),
    path("<slug:venue_slug>/<int:year>/<int:month>/<int:day>/", date_page, name="date_page"),
    path("start_payment/", start_payment, name="start_payment"),
    path("create-payment-intent/", create_payment_intent, name="create-payment-intent"),
    path("phase1-report/", phase1_report, name="phase1_report"),
    path("<slug:venue_slug>/", venue, name="venue"),
]
