"""governance/kyc/views/dashboard.py — role-aware KYC dashboard (thin view)."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from governance.kyc.selectors import dashboard as dashboard_selectors


@login_required
def kyc_dashboard(request):
    """Render counts + recent applications, scoped by role/market in the selector."""
    context = {
        "active_tab": "kyc",
        "counts": dashboard_selectors.status_counts(request.user),
        "recent_applications": dashboard_selectors.recent_applications(request.user),
    }
    return render(request, "kyc/dashboard.html", context)