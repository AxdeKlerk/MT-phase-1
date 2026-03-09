from django.contrib import admin
from django.urls import include, path
from core.views import home, stripe_webhook
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    # path("", home, name="home"), for pahse 2
    path("stripe/webhook/", stripe_webhook, name="stripe-webhook"),    
    path('gigs/', include('gigs.urls')),
    path("", home),
]
