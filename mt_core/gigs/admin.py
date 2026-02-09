from django.contrib import admin
from .models import Artist, Venue, Gig, Payment

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
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Gig)
class GigAdmin(admin.ModelAdmin):
    list_display = ('artist', 'venue', 'gig_date', 'created_at')
    search_fields = ('artist__name', 'venue__name')
    list_filter = ('gig_date', 'artist', 'venue')
    ordering = ('-gig_date',)
    list_select_related = ('artist', 'venue')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('artist','gig_date', 'amount', 'payment_date')
    search_fields = ('gig__artist__name', 'gig__venue__name')
    list_filter = ('payment_date', 'amount')
    ordering = ('-payment_date',)
    list_select_related = ('gig__artist', 'gig__venue')

