"""
governance/kyc/models/nominee.py

Nominees attached to an application. share_percentage is a required field.
"""
from django.db import models

from governance.kyc.choices import NomineeRelation
from governance.kyc.models.base import KYCAuditBase


class KYCNominee(KYCAuditBase):
    """A nominee declared on a KYC application."""

    nominee_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the nominee.",
    )
    application = models.ForeignKey(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="nominees",
        help_text="Application this nominee belongs to.",
    )
    nominee_name = models.CharField(
        max_length=150, help_text="Full name of the nominee."
    )
    relation = models.CharField(
        max_length=10,
        choices=NomineeRelation.choices,
        help_text="Relationship of the nominee to the applicant.",
    )
    national_id_number = models.CharField(
        max_length=80, help_text="Nominee national ID / CNIC number."
    )
    # TODO(KYC-NOM-001): Validate aggregate nominee shares at workflow/service level
    # so total nominee allocation follows final business rule (e.g. total = 100).
    share_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Nominee's share percentage (required; nominee shares validated as a set).",
    )

    class Meta:
        db_table = "px_kyc_nominee"
        verbose_name = "KYC Nominee"
        verbose_name_plural = "KYC Nominees"
        indexes = [
            models.Index(fields=["application"], name="ix_kyc_nominee_app"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(share_percentage__gte=0) & models.Q(share_percentage__lte=100),
                name="ck_kyc_nominee_share_0_100",
            ),
        ]

    def __str__(self) -> str:
        return f"Nominee {self.nominee_name} ({self.relation})"