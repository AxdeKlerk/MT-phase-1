from django.contrib import admin
from django.urls import include, path
from core.views import fallback_tip, stripe_webhook, home, trigger_500
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", home, name="home"),
    path("stripe/webhook/", stripe_webhook, name="stripe-webhook"),
    path('gigs/', include('gigs.urls')),
    path("fallback/", fallback_tip, name="fallback"),
    path("test-500/", trigger_500),
]

# To test the 500 page, visit https://moshtip.com/test-500/ which will raise a ZeroDivisionError. 
# This is only for testing purposes and should be removed in production.