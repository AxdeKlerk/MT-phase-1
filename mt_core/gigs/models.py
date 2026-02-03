from django.db import models

class Artist(models.Model):
    name = models.CharField(max_length=250, unique=True)
    payment_reference = models.CharField(
        max_length=255,
        blank=True, null=True,
        help_text="Square payment reference (required before activating gigs)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Gig(models.Model):
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE)
    gig_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("artist", "venue", "gig_date")
    
    def __str__(self):
       return f"{self.artist.name} at {self.venue.name} on {self.gig_date}"