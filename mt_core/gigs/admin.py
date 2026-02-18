from django.contrib import admin
from .models import Artist, Venue, Gig, Payment, ScanEvent, PaymentIntent

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


@admin.register(ScanEvent)
class ScanEventAdmin(admin.ModelAdmin):
    list_display = ('gig', 'format', 'fee_model', 'intent_count', 'success_count', 'created_at')
    list_filter = ('format', 'fee_model', 'gig')
    search_fields = ('session_key', 'gig__artist__name', 'gig__venue__name')
    ordering = ('-created_at',)
    list_select_related = ('gig',)

    def intent_count(self, obj):
        return obj.payment_intents.count()
    intent_count.short_description = "Payment Intents"

    def success_count(self, obj):
        return obj.payment_intents.filter(status="succeeded").count()
    success_count.short_description = "Successful Payments"



@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    list_display = (
        'stripe_payment_intent_id',
        'gig_name',
        'format',
        'fee_model',
        'scan_event',
        'amount',
        'status',
        'created_at'
    )
    list_filter = ('status', 'scan_event__fee_model', 'scan_event__format')
    ordering = ('-created_at',)
    list_select_related = ('scan_event', 'scan_event__gig')

    def gig_name(self, obj):
        return obj.scan_event.gig
    gig_name.short_description = "Gig"

    def format(self, obj):
        return obj.scan_event.format
    format.short_description = "Format"

    def fee_model(self, obj):
        return obj.scan_event.fee_model
    fee_model.short_description = "Fee Model"


