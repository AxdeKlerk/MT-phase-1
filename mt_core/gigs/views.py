import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
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

@require_POST
def start_payment(request):
    try:
        data = json.loads(request.body)
        gig_id = data.get("gig_id")
        amount = data.get("amount")
    except json.JSONDecodeError:
        return(JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400))
    
    # Validate Gig
    gig = get_object_or_404(Gig.objects.select_related("artist"), pk=gig_id)
    

    #Enforce Business Rules
    if not gig.artist.is_active:
        return JsonResponse({"status": "error", "message": "Artist is not active"}, status=400)
    
    #Stub Success Response
    if amount not in [2, 5, 10]:  # Validate amount
        return JsonResponse({"status": "error", "message": "Invalid tip amount"}, status=400)

    return JsonResponse({"status": "success", "message": "Payment initiated successfully"})
