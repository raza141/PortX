"""
governance/kyc/models/application.py

The KYC spine. Owns the application lifecycle and is the single source of truth
for compliance status. Links to the owning auth user (required) and, once
onboarding reaches the right point, to a CRM Investor (nullable).
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from governance.kyc.choices import (
    AccountHoldingType,
    ApplicationStatus,
    ClientClassification,
    InitiationChannel,
    Market,
    PersonType,
    RiskRating,
)
from governance.kyc.models.base import KYCAuditBase


class KYCApplication(KYCAuditBase):
    """A single individual KYC application (one per onboarding attempt/version)."""

    application_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the KYC application.",
    )
    # --- Ownership ---------------------------------------------------------- #
    owner_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="kyc_applications",
        help_text="Authenticated user who owns this application (required).",
    )
    investor = models.ForeignKey(
        "crm.Investor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kyc_applications",
        help_text="Linked CRM investor; null until handoff creates or links it on approval.",
    )
    referral_source = models.ForeignKey(
        "kyc.KYCReferralSource",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
        help_text="How the applicant was sourced (internal, distributor, or direct).",
    )
    # --- Identity of the application ---------------------------------------
    application_number = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Generated reference, e.g. PSX-KYC-2026-000001.",
    )
    onboarding_market = models.ForeignKey(
        "masters.ExecutionVenue",
        on_delete=models.PROTECT,
        related_name="kyc_applications",
        help_text="Business onboarding lane for this application.",
    )
    application_status = models.CharField(
        max_length=16,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        db_index=True,
        help_text="Current lifecycle status; mutated only by workflow services.",
    )
    # --- Classification ----------------------------------------------------- #
    account_holding_type = models.CharField(
        max_length=8,
        choices=AccountHoldingType.choices,
        default=AccountHoldingType.SINGLE,
        help_text="Single or joint holding; JOINT enables the joint-holder subsection.",
    )
    person_type = models.CharField(
        max_length=12,
        choices=PersonType.choices,
        default=PersonType.INDIVIDUAL,
        editable=False,
        help_text="Always INDIVIDUAL in Phase 1; reserved for the corporate phase.",
    )
    client_classification = models.CharField(
        max_length=3,
        choices=ClientClassification.choices,
        default=ClientClassification.RETAIL,
        help_text="Regulatory client classification.",
    )
    initiation_channel = models.CharField(
        max_length=12,
        choices=InitiationChannel.choices,
        default=InitiationChannel.SELF,
        help_text="Whether onboarding was self-service or RM-assisted.",
    )
    # --- Dates / risk ------------------------------------------------------- #
    kyc_opening_date = models.DateField(
        default=timezone.localdate,
        help_text="Date the KYC process was initiated, not the account activation date.",
    )
    aml_risk_rating = models.CharField(
        max_length=1,
        choices=RiskRating.choices,
        null=True,
        blank=True,
        help_text="AML / compliance screening risk; set during review (not suitability).",
    )
    # --- Extensibility / versioning ---------------------------------------- #
    market_extra = models.JSONField(
        default=dict,
        blank=True,
        help_text="Documented low-query market-specific edge-case data only.",
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="Re-KYC version number; increments on supersede.",
    )
    supersedes = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superseded_by",
        help_text="Prior application version this one replaces.",
    )

    class Meta:
        db_table = "px_kyc_application"
        verbose_name = "KYC Application"
        verbose_name_plural = "KYC Applications"
        indexes = [
            models.Index(fields=["onboarding_market", "application_status"], name="ix_kyc_app_market_status"),
        ]
    def clean(self):
        """Validate application lineage and reserved-field rules."""
        if self.supersedes_id and self.supersedes_id == self.application_id:
            raise ValidationError({"supersedes": "An application cannot supersede itself."})

    def __str__(self) -> str:
        return f"{self.application_number} [{self.application_status}]"