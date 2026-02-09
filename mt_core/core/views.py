from django.shortcuts import redirect
from gigs.models import Gig
from datetime import date


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