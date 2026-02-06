from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Venue, Gig, Artist
from datetime import date

def date_page(request, venue_slug, year, month, day):
    venue = get_object_or_404(Venue, slug=venue_slug)
    gig_date = date(year, month, day)
    gigs = (
        Gig.objects
        .filter(venue=venue, gig_date=gig_date)
        .select_related("artist")
        .order_by("artist__name")
    )

    context = {
        "venue": venue,
        "gig_date": gig_date,
        "gigs": gigs,
    }

    return render(request, "gigs/date_page.html", context)

def tip_page(request, gig_id):
    gig = get_object_or_404(
        Gig.objects.select_related("artist", "venue"),
        pk=gig_id
    )

    context = {
        "gig": gig,
        "artist": gig.artist,
        "venue": gig.venue,
        "gig_date": gig.gig_date,
        "amounts": [2, 5, 10],  # placeholder amounts
    }

    return render(request, "gigs/tip_page.html", context)

