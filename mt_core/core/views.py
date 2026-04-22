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
import logging
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

def home(request):
    gig = (
        Gig.objects
        .filter(gig_date__gte=date.today())
        .select_related("venue")
        .order_by("gig_date")
        .first()
        )

    if gig and gig.venue:
        return redirect("gigs:venue", venue_slug=gig.venue.slug)
    
    return redirect("fallback")

@csrf_exempt
def stripe_webhook(request):

    logger.debug("Webhook hit")

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
        logger.error("Webhook invalid payload: %s", e)
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error("Webhook signature verification failed: %s", e)
        return HttpResponse(status=400)

    # If we reach here → signature is valid
    logger.debug("Webhook received and verified")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        processor_id = payment_intent["id"]
        amount_received = payment_intent["amount_received"]  # in pence
        metadata = payment_intent.get("metadata", {})
        tip_amount = metadata.get("tip_amount")
        tip_amount = Decimal(tip_amount) if tip_amount else None
        gig_id = metadata.get("gig_id")
        
        if not gig_id:
            logger.warning("Missing gig_id in metadata: %s", processor_id)
            return HttpResponse(status=200)
                
        logger.debug("Looking for PaymentIntent: %s", processor_id)

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
            logger.debug("PaymentIntent created via webhook: %s", processor_id)
        
        # Fallback: attach ScanEvent if missing and gig_id is available
        # This only applies if no ScanEvent is linked.
        # In normal flow, ScanEvent is created on page load,
        # so this should rarely (if ever) trigger.

        # NOTE:
        # This is a best-effort fallback.
        # It attaches the most recent ScanEvent for the gig,
        # not necessarily the exact one for this payer.
        if pi.scan_event is None:

            scan_event = (
                ScanEvent.objects
                .filter(gig_id=gig_id)
                .order_by("-created_at")
                .first()
            )

            logger.debug("Fallback ScanEvent search for gig %s: %s", gig_id, scan_event)

            if scan_event:
                pi.scan_event = scan_event
                pi.save()
                logger.debug("ScanEvent attached via fallback: %s", processor_id)
            else:
                logger.debug("No ScanEvent found for fallback: %s", processor_id)

        # Idempotency check
        if Payment.objects.filter(processor_id=processor_id).exists():
            
            logger.debug("Duplicate webhook ignored: %s", processor_id)
            return HttpResponse(status=200)
        
        # Convert pence to Decimal pounds safely
        amount = Decimal(amount_received) / Decimal("100")

        # Fetch Gig safely
        try:
            gig = Gig.objects.get(pk=gig_id)
        except Gig.DoesNotExist:
            logger.warning("Gig not found: %s", gig_id)
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
            logger.debug("Ledger write complete: %s", processor_id)
        except IntegrityError:
            logger.debug("Race condition prevented duplicate write: %s", processor_id)
            return HttpResponse(status=200)

        logger.debug("Payment confirmed: %s", processor_id)

    return HttpResponse(status=200)

def fallback_tip(request):
    gig = (
        Gig.objects
        .filter(gig_date__gte=date.today())
        .select_related("venue")
        .order_by("gig_date")
        .first()
    )

    if not gig:
        gig = (
            Gig.objects
            .select_related("venue")
            .order_by("-gig_date")
            .first()
        )

    if gig and gig.venue:
        return redirect("gigs:venue", venue_slug=gig.venue.slug)

    return HttpResponse("No gigs available ... yet!")

def trigger_500(request):
    return 1 / 0