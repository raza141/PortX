"""
governance/kyc/services/screening_stub.py

Phase-2 placeholder. Records a PENDING third-party check without calling any
external provider. The real integration plugs in here later with no schema change.
"""
from __future__ import annotations

from django.utils import timezone

from governance.kyc.choices import ScreeningOutcome


def request_screening(application, provider, actor):
    """Create a PENDING screening record (no live integration in Phase 1)."""
    from governance.kyc.models import KYCThirdPartyCheck

    return KYCThirdPartyCheck.objects.create(
        application=application,
        provider=provider,
        outcome=ScreeningOutcome.PENDING,
        requested_at=timezone.now(),
        raw_response={},
        created_by=actor,
    )