from django.contrib import admin
from .models import Artist, Venue, Gig

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('name', 'is_active')

@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name',)
    list_filter = ('name', 'is_active')

@admin.register(Gig)
class GigAdmin(admin.ModelAdmin):
    list_display = ('artist', 'venue', 'gig_date', 'created_at')
    search_fields = ('artist__name', 'venue__name')
    list_filter = ('gig_date', 'artist__name', 'venue__name')