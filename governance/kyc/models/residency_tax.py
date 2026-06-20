"""
governance/kyc/models/residency_tax.py

One row per (country, TIN) tax residency. Serves the principal and joint holders
through the nullable joint_holder FK. Replaces the flat Residency A/B/C columns.
"""
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError

from governance.kyc.models.base import KYCAuditBase


class KYCResidencyTax(KYCAuditBase):
    """A single tax-residency declaration (country + TIN) for a holder."""

    residency_tax_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the tax-residency row.",
    )
    application = models.ForeignKey(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="residency_tax_rows",
        help_text="Application this tax-residency row belongs to.",
    )
    joint_holder = models.ForeignKey(
        "kyc.KYCJointHolder",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="residency_tax_rows",
        help_text="Owning joint holder; null means the row belongs to the principal.",
    )
    country = models.ForeignKey(
        "masters.Country",
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="kyc_tax_residencies",
        help_text="Country of tax residency (FK to reference country).",
    )
    tax_identification_number = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        help_text="TIN for this country; required unless an unavailable reason is given.",
    )
    tin_unavailable_reason = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Reason a TIN is not provided (per CRS reason categories).",
    )

    class Meta:
        db_table = "px_kyc_residency_tax"
        verbose_name = "KYC Tax Residency"
        verbose_name_plural = "KYC Tax Residencies"
        indexes = [
            models.Index(fields=["application", "joint_holder"], name="ix_kyc_taxres_app_jh"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(tax_identification_number__isnull=False)
                          | Q(tin_unavailable_reason__isnull=False),
                name="ck_kyc_taxres_tin_or_reason",
            ),
        ]

    def clean(self):
        if self.joint_holder_id and self.joint_holder.application_id != self.application_id:
            raise ValidationError(
                {"joint_holder": "Joint holder must belong to the same application."}
            )

        # TODO(KYC-TAX-RES-001): Restrict tin_unavailable_reason to controlled CRS reason codes
        # (e.g. A/B/C + optional explanation text where required).

        # TODO(KYC-TAX-RES-002): Decide uniqueness policy for country per owner
        # and add UniqueConstraint once duplicate handling is finalized.

    def __str__(self) -> str:
        return f"TaxRes(country {self.country_id}, app {self.application_id})"