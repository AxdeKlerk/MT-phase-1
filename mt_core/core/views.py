import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from gigs.models import Gig, Payment, PaymentIntent, ScanEvent
from datetime import date
from decimal import Decimal
from django.db import IntegrityError
from django.utils import timezone

stripe.api_key = settings.STRIPE_SECRET_KEY

def home(request):
    gig = (
        Gig.objects
        .filter(gig_date__gte=date.today())
        .select_related("venue")
        .order_by("gig_date")
        .first()
        )

    if gig:
        return redirect("gigs:venue", venue_slug=gig.venue.slug)
    
    return redirect("/admin/")


@csrf_exempt
def stripe_webhook(request):

    print("WEBHOOK HIT")

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        print("ValueError:", e)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print("SignatureVerificationError:", e)
        return HttpResponse(status=400)

    # If we reach here → signature is valid
    print("Webhook received and verified")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        processor_id = payment_intent["id"]
        amount_received = payment_intent["amount_received"]  # in pence
        metadata = payment_intent.get("metadata", {})
        tip_amount = metadata.get("tip_amount")
        tip_amount = Decimal(tip_amount) if tip_amount else None
        gig_id = metadata.get("gig_id")
        
        if not gig_id:
            print(f"Missing gig_id in metadata for {processor_id}")
            return HttpResponse(status=200)
                
        print("Looking for PaymentIntent with ID:", processor_id)

        # Update or create PaymentIntent tracking record
        pi, created = PaymentIntent.objects.get_or_create(
            stripe_payment_intent_id=processor_id,
            defaults={
                "amount": amount_received,
                "status": "succeeded",
                "completed_at": timezone.now(),
                "scan_event": None,
            }
        )

        if not created:
            pi.status = "succeeded"
            pi.completed_at = timezone.now()
            pi.save()
        else:
            print(f"PaymentIntent created via webhook for {processor_id}")
        
        # Fallback: attach ScanEvent if missing and gig_id is available
        if pi.scan_event is None:

            scan_event = (
                ScanEvent.objects
                .filter(gig_id=gig_id)
                .order_by("-created_at")
                .first()
            )

            print(f"Fallback search for gig {gig_id} returned:", scan_event)

            if scan_event:
                pi.scan_event = scan_event
                pi.save()
                print(f"ScanEvent attached via fallback for {processor_id}")
            else:
                print(f"No ScanEvent found for fallback on {processor_id}")

        # Idempotency check
        if Payment.objects.filter(processor_id=processor_id).exists():
            print(f"Duplicate webhook ignored for {processor_id}")
            return HttpResponse(status=200)
        
        # Convert pence to Decimal pounds safely
        amount = Decimal(amount_received) / Decimal("100")

        # Fetch Gig safely
        try:
            gig = Gig.objects.get(pk=gig_id)
        except Gig.DoesNotExist:
            print(f"Gig {gig_id} not found")
            return HttpResponse(status=400)
        
        # Create Payment record
        try:
            Payment.objects.create(
                gig=gig,
                amount=amount,
                tip_amount=tip_amount,
                processor_id=processor_id,
                status="successful",
            )
            print(f"Ledger write complete for {processor_id}")
        except IntegrityError:
            print(f"Race condition prevented duplicate write for {processor_id}")
            return HttpResponse(status=200)

        print(f"E3 CONFIRMED for processor ID: {processor_id}")

    return HttpResponse(status=200)

