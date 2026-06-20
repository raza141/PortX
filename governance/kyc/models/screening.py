"""
governance/kyc/models/screening.py

Phase-2 screening stub. The table and FKs exist now so World-Check / document /
liveness integrations plug in later with no schema migration of the enum surface.
No live integration is wired in Phase 1.
"""
from django.db import models

from governance.kyc.choices import ScreeningOutcome, ScreeningProvider
from governance.kyc.models.base import KYCAuditBase


class KYCThirdPartyCheck(KYCAuditBase):
    """A third-party screening/verification check against an application."""

    third_party_check_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the screening check.",
    )
    application = models.ForeignKey(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="third_party_checks",
        help_text="Application this check was run against.",
    )
    # TODO(KYC-SCREEN-001): Enforce outcome/timestamp consistency once live provider
    # integrations are enabled (e.g. PENDING => completed_at is null).
    provider = models.CharField(
        max_length=16,
        choices=ScreeningProvider.choices,
        help_text="Screening provider (World-Check, document API, liveness).",
    )
    outcome = models.CharField(
        max_length=10,
        choices=ScreeningOutcome.choices,
        default=ScreeningOutcome.PENDING,
        help_text="Result of the check; defaults to Pending.",
    )
    reference = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        help_text="Provider-side reference/case id.",
    )
    # TODO(KYC-SCREEN-002): Consider extracting normalized decision fields
    # from raw_response once provider contracts are stable.
    raw_response = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw provider payload, retained for audit (Phase 2).",
    )
    requested_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp the check was requested."
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp the check completed."
    )

    class Meta:
        db_table = "px_kyc_third_party_check"
        verbose_name = "KYC Third-Party Check"
        verbose_name_plural = "KYC Third-Party Checks"
        indexes = [
            models.Index(fields=["application", "provider"], name="ix_kyc_tpc_app_provider"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(requested_at__isnull=True)
                          | models.Q(completed_at__isnull=True)
                          | models.Q(completed_at__gte=models.F("requested_at")),
                name="ck_kyc_tpc_completed_after_requested",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.outcome} (app {self.application_id})"