"""
governance/kyc/services/application_number.py

Allocates the application number `{MARKET}-KYC-{YEAR}-{NNNNNN}`, sequenced
per-market-per-year, 6-digit zero-padded. Allocation happens at initiation.

Concurrency: the sequence is derived under a row lock on existing rows for the
(market, year) partition, and the unique constraint on `application_number` is
the final backstop — on the rare race, allocation retries.
"""
from __future__ import annotations

from django.db import IntegrityError, transaction
from django.utils import timezone

from governance.kyc.constants import (
    APPLICATION_NUMBER_SEQUENCE_WIDTH,
    APPLICATION_NUMBER_TEMPLATE,
)
from governance.kyc.services.exceptions import ApplicationNumberError

_MAX_RETRIES = 5


def _format(market: str, year: int, sequence: int) -> str:
    return APPLICATION_NUMBER_TEMPLATE.format(market=market, year=year, sequence=sequence)


def peek_next(market: str, year: int | None = None) -> str:
    """Return the next number without persisting (for previews). Not race-safe."""
    from governance.kyc.models import KYCApplication

    year = year or timezone.localdate().year
    prefix = f"{market}-"
    last = (
        KYCApplication.objects.filter(onboarding_market__code=market, application_number__startswith=prefix)
        .filter(application_number__contains=f"-{year}-")
        .order_by("-application_number")
        .values_list("application_number", flat=True)
        .first()
    )
    next_seq = (int(last.split("-")[-1]) + 1) if last else 1
    return _format(market, year, next_seq)


def allocate(market: str, year: int | None = None) -> str:
    """
    Allocate the next application number for the market/year, race-safe.

    Must be called inside (or will open) an atomic block; the caller normally
    creates the KYCApplication in the same transaction.
    """
    from governance.kyc.models import KYCApplication

    year = year or timezone.localdate().year

    for _ in range(_MAX_RETRIES):
        try:
            with transaction.atomic():
                rows = list(
                    KYCApplication.objects.select_for_update()
                    .filter(onboarding_market__code=market, application_number__contains=f"-{year}-")
                    .values_list("application_number", flat=True)
                )
                max_seq = 0
                for number in rows:
                    try:
                        max_seq = max(max_seq, int(number.split("-")[-1]))
                    except (ValueError, IndexError):
                        continue
                candidate = _format(market, year, max_seq + 1)
                # Probe uniqueness; the DB unique constraint is the real guarantee.
                if not KYCApplication.objects.filter(application_number=candidate).exists():
                    return candidate
        except IntegrityError:
            continue
    raise ApplicationNumberError(
        f"Could not allocate application number for {market}/{year} after {_MAX_RETRIES} tries."
    )