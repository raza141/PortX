"""
governance/kyc/models/source_of_wealth.py

Primary source-of-wealth record. source_of_wealth (origin of accumulated wealth)
and source_of_funds (origin of the funds being invested) are kept as distinct
AML fields. One primary record now; extensible to itemized sub-records later
without destructive redesign.
"""
from django.db import models

from governance.kyc.choices import (
    FBRCategory, SourceClassification, ZakatStatus, SourceOfWealthType, SourceOfFundsType
    )
from governance.kyc.models.base import KYCAuditBase


class KYCSourceOfWealth(KYCAuditBase):
    """One-to-one source-of-wealth/funds record for a KYC application."""


    source_of_wealth_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the source-of-wealth record.",
    )
    application = models.OneToOneField(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="source_of_wealth",
        help_text="Application this source-of-wealth record belongs to (1:1).",
    )
    source_of_wealth = models.CharField(
        max_length=20,
        choices=SourceOfWealthType.choices,
        default=SourceOfWealthType.SALARY,
        help_text="Origin of the applicant's overall wealth (e.g. business, inheritance).",
    )
    source_of_funds = models.CharField(
        max_length=20,
        choices=SourceOfFundsType.choices,
        default=SourceOfFundsType.SALARY,
        help_text="Origin of the funds being invested (e.g. salary, sale proceeds).",
    )
    source_classification = models.CharField(
        max_length=12,
        choices=SourceClassification.choices,
        default=SourceClassification.INDIVIDUAL,
        help_text="Whether the source is individual or corporate in nature.",
    )
    # PSX-gated
    fbr_category = models.CharField(
        max_length=10,
        choices=FBRCategory.choices,
        null=True,
        blank=True,
        help_text="Pakistan FBR filing status (PSX market).",
    )
    zakat_status = models.CharField(
        max_length=16,
        choices=ZakatStatus.choices,
        null=True,
        blank=True,
        help_text="Zakat applicability (PSX market).",
    )

    class Meta:
        db_table = "px_kyc_source_of_wealth"
        verbose_name = "KYC Source of Wealth"
        verbose_name_plural = "KYC Sources of Wealth"

    def __str__(self) -> str:
        return f"SoW(app {self.application_id})"