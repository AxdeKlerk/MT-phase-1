import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from .models import Venue, Gig, Artist, Payment, ScanEvent, PaymentIntent
from datetime import date
from decimal import Decimal
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.db.models.functions import ExtractHour
from django.contrib.admin.views.decorators import staff_member_required

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

    context = {
        "gig": gig,
        "artist": gig.artist,
        "venue": gig.venue,
        "gig_date": gig.gig_date,
        "amounts": [2, 5, 10],  # placeholder amounts
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLISHABLE_KEY,
        "cover_processing_fees": gig.cover_processing_fees,
    }

    # Ensure session exists
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    # Check existing scan
    existing_scan = ScanEvent.objects.filter(
        gig=gig,
        session_key=session_key
    ).first()

    if not existing_scan:

        fee_model_snapshot = "absorbed" if gig.cover_processing_fees else "fan_pays"

        ScanEvent.objects.create(
            gig=gig,
            session_key=session_key,
            format=request.GET.get("format", "poster"),
            fee_model=fee_model_snapshot
        )

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
        fee = (amount_decimal * Decimal("0.014")) + Decimal("0.20")
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
            "gig_id": str(gig_id),
            "artist_name": gig.artist.name,
            "tip_amount": amount
        }
    )

    # Ensure session exists
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    # Get related ScanEvent
    scan_event = ScanEvent.objects.filter(
        gig=gig,
        session_key=session_key
    ).first()

    # Check for existing successful PaymentIntent for this session and gig
    existing_success = PaymentIntent.objects.filter(
        scan_event__isnull=False,
        scan_event__session_key=session_key,
        status="succeeded"
    ).exists()

    # Create PaymentIntent tracking record
    PaymentIntent.objects.create(
        scan_event=scan_event if scan_event else None,
        stripe_payment_intent_id=intent.id,
        amount=amount_pence,
        status="created",
        is_repeat=existing_success
    )

    # Return response
    return JsonResponse({
        "client_secret": intent.client_secret,
        "total_amount": str(total.quantize(Decimal("0.01"))),
        "fee_amount": str(fee.quantize(Decimal("0.01"))),
        "cover_processing_fees": gig.cover_processing_fees,
    })


@staff_member_required
def phase1_report(request):

    from .models import ScanEvent, PaymentIntent, Payment

    # SECTION 1 — Condition Level Metrics
    condition_data = []

    for condition in ["poster", "card", "unknown"]:

        scans = ScanEvent.objects.filter(format=condition)

        scan_count = scans.count()

        if condition == "unknown":
            intents = PaymentIntent.objects.filter(scan_event__isnull=True)
        else:
            intents = PaymentIntent.objects.filter(scan_event__format=condition)

        intent_count = intents.count()

        successes = intents.filter(status="succeeded")

        success_count = successes.count()

        repeat_count = successes.filter(is_repeat=True).count()
        repeat_rate = (repeat_count / success_count * 100) if success_count else 0

        avg_tip = Payment.objects.filter(
            processor_id__in=successes.values_list(
                "stripe_payment_intent_id",
                flat=True
            )
        ).aggregate(avg=Avg("amount"))["avg"]

        condition_data.append({
            "condition": condition,
            "scan_count": scan_count,
            "intent_count": intent_count,
            "success_count": success_count,
            "scan_to_intent": (intent_count / scan_count * 100) if scan_count else 0,
            "avg_tip": avg_tip or 0,
            "tips_per_100_scans": (success_count / scan_count * 100) if scan_count else 0,
            "repeat_count": repeat_count,
            "repeat_rate": round(repeat_rate, 2),

        })

    # SECTION 2 — Artist Totals
    artist_totals = (
        Payment.objects
        .values("gig__artist__name")
        .annotate(
            total_tips=Count("id"),
            total_value=Sum("amount"),
            average_tip=Avg("amount")
        )
        .order_by("-total_value")
    )

    # SECTION 3 — Chronological Tip Log for Phase 2 (Not currently displayed)
    #tip_log = (
        #Payment.objects
        #.select_related("gig__artist", "gig__venue")
        #.order_by("-payment_date")
    #)

    # SECTION 4 — Time of Day Distribution (Successful Only)
    time_distribution = (
        Payment.objects
        .annotate(hour=ExtractHour("payment_date"))
        .values("hour")
        .annotate(
            tip_count=Count("id"),
            total_value=Sum("amount")
        )
        .order_by("hour")
    )

    total_payments = Payment.objects.count()

    total_revenue = Payment.objects.aggregate(
        total=Sum("amount")
    )["total"] or 0

    total_scans = sum(item["scan_count"] for item in condition_data)
    total_success = sum(item["success_count"] for item in condition_data)

    overall_tips_per_100 = (
        (total_success / total_scans) * 100
        if total_scans else 0
    )

    context = {
        "condition_data": condition_data,
        "artist_totals": artist_totals,
        #"tip_log": tip_log, For Phase 2
        "time_distribution": time_distribution,
        "total_payments": total_payments,
        "total_revenue": total_revenue,
        "overall_tips_per_100": overall_tips_per_100,
    }

    return render(request, "gigs/phase1_report.html", context)
