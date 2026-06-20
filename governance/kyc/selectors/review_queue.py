"""
governance/kyc/selectors/review_queue.py

Read-only query logic for the compliance/management review queue.
"""
from __future__ import annotations

from governance.kyc import permissions
from governance.kyc.choices import ApplicationStatus
from governance.kyc.selectors.dashboard import base_queryset_for

REVIEW_STATES = [
    ApplicationStatus.SUBMITTED,
    ApplicationStatus.UNDER_REVIEW,
    ApplicationStatus.ADDL_INFO,
    ApplicationStatus.ESCALATED,
]


def review_queue(user):
    """Applications awaiting review/decision within the user's scope."""
    if not (
        permissions.is_compliance(user)
        or permissions.is_senior_mgmt(user)
        or permissions.is_admin(user)
    ):
        from governance.kyc.models import KYCApplication

        return KYCApplication.objects.none()
    return (
        base_queryset_for(user)
        .filter(application_status__in=REVIEW_STATES)
        .select_related("personal_info", "owner_user")
        .order_by("kyc_opening_date")
    )


def escalated_queue(user):
    """Escalated applications only (management focus)."""
    return review_queue(user).filter(application_status=ApplicationStatus.ESCALATED)