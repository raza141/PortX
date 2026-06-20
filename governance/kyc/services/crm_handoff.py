"""
governance/kyc/services/crm_handoff.py

Minimal, one-way KYC -> CRM handoff. On approval, ensure a CRM Investor exists and
is linked to the application. Only the minimum needed for investor/account
readiness crosses the boundary; KYC remains the source of truth and there is no
reverse sync.
"""
from __future__ import annotations

from django.db import transaction


@transaction.atomic
def on_approved(application, actor):
    """Create or link a CRM Investor for an approved application (idempotent)."""
    if application.investor_id:
        return application.investor

    from governance.crm.models import Investor  # local import to avoid hard coupling at import time

    personal = getattr(application, "personal_info", None)
    full_name = (
        f"{personal.first_name} {personal.last_name}".strip()
        if personal
        else application.application_number
    )
    email = personal.email if personal else None

    investor, _ = Investor.objects.get_or_create(
        email=email,
        defaults={
            "inv_nm": full_name,
            "client_class_cd": application.client_classification,
        },
    )

    application.investor = investor
    application.updated_by = actor
    application.save(update_fields=["investor", "updated_by", "updated_at"])
    return investor