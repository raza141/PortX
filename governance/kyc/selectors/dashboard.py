"""
governance/kyc/selectors/dashboard.py

Read-only query logic for the KYC dashboard. Scopes results by the viewer's role
and market (clients see only their own applications).
"""
from __future__ import annotations

from django.db.models import Count

from governance.kyc import permissions
from governance.kyc.choices import ApplicationStatus


def base_queryset_for(user):
    """Applications visible to this user (owner / market-scoped staff / admin)."""
    from governance.kyc.models import KYCApplication

    qs = KYCApplication.objects.all()
    if permissions.is_admin(user):
        return qs
    if permissions.is_compliance(user) or permissions.is_senior_mgmt(user) or permissions.is_rm(user):
        market = permissions.staff_market(user)
        if market and market != "ALL":
            qs = qs.filter(onboarding_market__code=market)
        return qs
    return qs.filter(owner_user=user)


def status_counts(user) -> dict:
    """Count of visible applications per status (zero-filled)."""
    counts = {status.value: 0 for status in ApplicationStatus}
    rows = (
        base_queryset_for(user)
        .values("application_status")
        .annotate(n=Count("application_id"))
    )
    for row in rows:
        counts[row["application_status"]] = row["n"]

    counts["total"] = sum(counts[s.value] for s in ApplicationStatus)
    counts["pending_review"] = (
        counts[ApplicationStatus.SUBMITTED.value]
        + counts[ApplicationStatus.UNDER_REVIEW.value]
        + counts[ApplicationStatus.ADDL_INFO.value]
        + counts[ApplicationStatus.ESCALATED.value]
    )
    return counts


def recent_applications(user, limit: int = 10):
    from governance.kyc.models import KYCPersonalInfo

    apps = (
        base_queryset_for(user)
        .select_related("owner_user", "personal_info")
        .order_by("-updated_at")[:limit]
    )

    for app in apps:
        try:
            personal = app.personal_info
            app.applicant_name = f"{personal.first_name} {personal.last_name}".strip()
        except KYCPersonalInfo.DoesNotExist:
            app.applicant_name = ""
    return apps