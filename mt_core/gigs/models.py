from django.db import models
from cloudinary.models import CloudinaryField
from decimal import Decimal


class Artist(models.Model):
    name = models.CharField(max_length=250, unique=True)
    payment_reference = models.CharField(
        max_length=255,
        blank=True, null=True,
        help_text="Square payment reference (required before activating gigs)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    logo = CloudinaryField('artist_logos', blank=True, null=True)

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Gig(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    gig_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    play_order = models.PositiveIntegerField(
        default=0, help_text="Order in which venues are displayed")
    cover_processing_fees = models.BooleanField(
        default=False, help_text="If true, MT will cover payment processing fees for this gig")

    class Meta:
        unique_together = ("artist", "venue", "gig_date")
    
    def __str__(self):
        return f"{self.artist} at {self.venue} on {self.gig_date}"
    
class Payment(models.Model):
    gig = models.ForeignKey(Gig, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=5, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=255, blank=True, null=True)
    processor_id = models.CharField(max_length=255, unique=True, blank=True, null=True)

    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    @property
    def artist(self):
        return self.gig.artist

    @property
    def venue(self):
        return self.gig.venue

    @property
    def gig_date(self):
        return self.gig.gig_date
    
    @property
    def is_successful(self):
        return self.status == 'successful'
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def amount_in_pence(self):
        return int(self.amount * Decimal(100))

    def __str__(self):
        return f"Payment of £{self.amount} for {self.artist} at {self.venue} on {self.gig_date}"


class ScanEvent(models.Model):

    FORMAT_CHOICES = [
        ("poster", "Poster"),
        ("card", "Card"),
    ]

    gig = models.ForeignKey(
        Gig,
        on_delete=models.CASCADE,
        related_name="scan_events"
    )

    session_key = models.CharField(max_length=40)

    format = models.CharField(
        max_length=20,
        choices=FORMAT_CHOICES
    )

    # Snapshot at time of scan
    fee_model = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["gig", "session_key"],
                name="unique_scan_per_session_per_gig"
            )
        ]

    def __str__(self):
        return f"Scan - {self.gig} - {self.session_key}"


class PaymentIntent(models.Model):

    STATUS_CHOICES = [
        ("created", "Created"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    ]

    scan_event = models.ForeignKey(
        ScanEvent,
        on_delete=models.CASCADE,
        related_name="payment_intents"
    )

    stripe_payment_intent_id = models.CharField(
        max_length=255,
        unique=True
    )

    amount = models.PositiveIntegerField(
        help_text="Amount in pence"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="created"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.stripe_payment_intent_id} - {self.status}"
