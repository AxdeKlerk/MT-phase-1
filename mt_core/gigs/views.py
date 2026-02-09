from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Venue, Gig
from datetime import date

def date_page(request, venue_slug, year, month, day):
    venue = get_object_or_404(Venue, slug=venue_slug)
    gig_date = date(year, month, day)
    gigs = (
        Gig.objects
        .filter(venue=venue, gig_date=gig_date, artist__is_active=True)
        .select_related("artist")
        .order_by("play_order")
    )

    context = {
        "venue": venue,
        "gig_date": gig_date,
        "gigs": gigs,
        "play_order" : gigs.first().play_order if gigs.exists() else None,
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


def venue(request, venue_slug):
    venue = get_object_or_404(Venue, slug=venue_slug)

    today = date.today()

    gigs = (
        Gig.objects
        .filter(venue=venue, gig_date__gte=today)
        .select_related("artist")
        .order_by("gig_date", "play_order")
    )

    next_gig_date = gigs.first().gig_date if gigs.exists() else None

    context = {
        "venue": venue,
        "gigs": gigs,
        "gig_date": next_gig_date,
    }

    return render(request, "gigs/date_page.html", context)

def payment_page(request, gig_id, amount):
    gig = get_object_or_404(
        Gig.objects.select_related("artist", "venue"),
        pk=gig_id
    )

    context = {
        "gig": gig,
        "artist": gig.artist,
        "venue": gig.venue,
        "gig_date": gig.gig_date,
        "amount": amount,
    }

    return render(request, "gigs/payment_page.html", context)