"""
governance/kyc/models/residence.py

Residence/address plus FATCA/CRS top-level flags. country is an FK to reference
data; province is nullable and jurisdiction-gated (NOT universal); region/city
master tables are a future enhancement and are not required in Phase 1.
"""
from django.db import models

from governance.kyc.choices import TaxApplicability
from governance.kyc.models.base import KYCAuditBase


class KYCResidence(KYCAuditBase):
    """One-to-one residence/tax-flag record for a KYC application."""

    residence_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the residence record.",
    )
    application = models.OneToOneField(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="residence",
        help_text="Application this residence record belongs to (1:1).",
    )

    permanent_address = models.TextField(
        help_text="Full permanent address (free text in Phase 1).",
    )
    permanent_country = models.ForeignKey(
        "masters.Country",
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="kyc_permanent_residences",
        help_text="Permanent address country (FK to reference country).",
    )
    # TODO(KYC-LOC-002): Consider migrating permanent_city to City master later.
    permanent_city = models.CharField(
        max_length=120,
        # null=True,
        blank=True,
        help_text="Permanent address city (free text; city master is a future enhancement).",
    )
    province = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        help_text="Province/state; surfaced only where the jurisdiction requires it.",
    )
    # TODO(KYC-RES-001): Enforce current_same_as_permanent vs current_residence_address consistency.
    current_residence_address = models.TextField(
        # null=True,
        blank=True,
        help_text="Current/mailing address when different from permanent.",
    )
    current_same_as_permanent = models.BooleanField(
        default=True,
        help_text="True if the current address equals the permanent address.",
    )
    # TODO(KYC-TAX-001): Align tax_status with FATCA/CRS flags when tax rules are final.
    tax_status = models.CharField(
        max_length=16,
        choices=TaxApplicability.choices,
        default=TaxApplicability.NON_APPLICABLE,
        help_text="Whether tax-residency reporting applies to the principal.",
    )
    fatca_applicable = models.BooleanField(
        default=False,
        help_text="True if FATCA reporting applies (US tax nexus).",
    )
    crs_applicable = models.BooleanField(
        default=False,
        help_text="True if CRS reporting applies.",
    )

    class Meta:
        db_table = "px_kyc_residency"
        verbose_name = "KYC Residence"
        verbose_name_plural = "KYC Residences"

    def __str__(self) -> str:
        return f"Residence(app {self.application_id})"