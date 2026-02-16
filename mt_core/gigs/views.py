import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from multiprocessing import context
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from .models import Venue, Gig, Artist, Payment
from datetime import date
from decimal import Decimal

stripe.api_key = settings.STRIPE_SECRET_KEY

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

    if gig.cover_processing_fees:
        fee_message = "No processing fees are being charged<br>for day 1 of this pilot!"
    else:
        fee_message = "Payment processor fee of (1.5% + 20p)<br>applies at checkout"

    context = {
        "gig": gig,
        "artist": gig.artist,
        "venue": gig.venue,
        "gig_date": gig.gig_date,
        "amounts": [2, 5, 10],  # placeholder amounts
        "fee_message": fee_message,
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLISHABLE_KEY,
        "cover_processing_fees": gig.cover_processing_fees,
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
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not gig_id or amount is None:
        return JsonResponse({"error": "Missing data"}, status=400)

    # Validate Gig
    gig = get_object_or_404(
        Gig.objects.select_related("artist"),
        pk=gig_id
    )

    # Enforce Business Rules
    if not gig.artist.is_active:
        return JsonResponse({"error": "Artist is not active"}, status=400)

    # Convert amount safely
    try:
        amount_decimal = Decimal(str(amount))
    except:
        return JsonResponse({"error": "Invalid amount format"}, status=400)

    # Validate allowed tip amounts
    allowed_amounts = [Decimal("2"), Decimal("5"), Decimal("10")]
    if amount_decimal not in allowed_amounts:
        return JsonResponse({"error": "Invalid tip amount"}, status=400)

    # Calculate fee and total
    if not gig.cover_processing_fees:
        fee = (amount_decimal * Decimal("0.015")) + Decimal("0.20")
        total = amount_decimal + fee
    else:
        fee = Decimal("0.00")
        total = amount_decimal

    # Convert to pence
    amount_pence = int((total * 100).to_integral_value())

    # Create PaymentIntent
    intent = stripe.PaymentIntent.create(
        amount=amount_pence,
        currency="gbp",
        payment_method_types=["card"],
        metadata={
            "gig_id": str(gig_id)
        }
    )

    # Return response
    return JsonResponse({
        "client_secret": intent.client_secret,
        "total_amount": str(total.quantize(Decimal("0.01"))),
        "fee_amount": str(fee.quantize(Decimal("0.01")))
    })


@csrf_exempt
def create_payment_intent(request):
    if request.method == "POST":
        gig_id = request.POST.get("gig_id")
        amount = request.POST.get("amount")

        if not gig_id or not amount:
            return JsonResponse({"error": "Missing data"}, status=400)

        try:
            amount_decimal = Decimal(amount)
            amount_pence = int(amount_decimal * 100)
        except:
            return JsonResponse({"error": "Invalid amount"}, status=400)

        intent = stripe.PaymentIntent.create(
            amount=amount_pence,
            currency="gbp",
            payment_method_types=["card"],
            metadata={
                "gig_id": gig_id
            }
        )

        return JsonResponse({
            "client_secret": intent.client_secret
        })

    return JsonResponse({"error": "Invalid request"}, status=400)
