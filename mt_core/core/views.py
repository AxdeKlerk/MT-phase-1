import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from gigs.models import Gig, Payment
from datetime import date

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
        return redirect(f"/gigs/{gig.venue.slug}/")

    return redirect("/admin/")

@csrf_exempt
def stripe_webhook(request):
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
        gig_id = metadata.get("gig_id")

        print("E3 CONFIRMED")
        print("Processor ID:", processor_id)
        print("Amount (pence):", amount_received)
        print("Gig ID from metadata:", gig_id)

        # Idempotency check
        if Payment.objects.filter(processor_id=processor_id).exists():
            print(f"Duplicate webhook ignored for {processor_id}")
            return HttpResponse(status=200)

        print(f"E3 CONFIRMED for processor ID: {processor_id}")

    return HttpResponse(status=200)
