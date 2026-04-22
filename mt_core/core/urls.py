from django.contrib import admin
from django.urls import include, path
from core.views import fallback_tip, stripe_webhook, home
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home, name="home"),
    path("stripe/webhook/", stripe_webhook, name="stripe-webhook"),
    path('gigs/', include('gigs.urls')),
    path("fallback/", fallback_tip, name="fallback"),
]
