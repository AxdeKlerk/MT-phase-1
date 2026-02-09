from django.db import models
from cloudinary.models import CloudinaryField

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

    class Meta:
        unique_together = ("artist", "venue", "gig_date")
    
    def __str__(self):
        return f"{self.artist} at {self.venue} on {self.gig_date}"
