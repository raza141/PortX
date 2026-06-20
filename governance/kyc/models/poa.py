"""
governance/kyc/models/poa.py

Power-of-attorney / authorized persons. Conditional on the application; the
document_type drives which supporting upload is required (see document_rules).
"""
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError

from governance.kyc.choices import POADocumentType
from governance.kyc.models.base import KYCAuditBase


class KYCPowerOfAttorney(KYCAuditBase):
    """An authorized person / power-of-attorney holder for an application."""

    poa_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the POA / authorized person.",
    )
    application = models.ForeignKey(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="power_of_attorney_holders",
        help_text="Application this authorized person belongs to.",
    )
    person_name = models.CharField(
        max_length=150, help_text="Authorized person's full name."
    )
    document_type = models.CharField(
        max_length=20,
        choices=POADocumentType.choices,
        help_text="Type of authorization document granting the POA.",
    )
    address = models.TextField(
        null=True, blank=True, help_text="Authorized person's address."
    )
    passport_number = models.CharField(
        max_length=80, null=True, blank=True, help_text="Authorized person's passport number."
    )
    passport_issue_date = models.DateField(
        null=True, blank=True, help_text="Passport issue date."
    )
    passport_expiry_date = models.DateField(
        null=True, blank=True, help_text="Passport expiry date."
    )
    national_id_number = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        help_text="Authorized person's national ID / CNIC / NICOP number.",
    )
    national_id_expiry_date = models.DateField(
        null=True, blank=True, help_text="National ID expiry date."
    )

    class Meta:
        db_table = "px_kyc_power_of_attorney"
        verbose_name = "KYC Power of Attorney"
        verbose_name_plural = "KYC Powers of Attorney"
        indexes = [
            models.Index(fields=["application"], name="ix_kyc_poa_app"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(passport_issue_date__isnull=True)
                | Q(passport_expiry_date__isnull=True)
                | Q(passport_expiry_date__gte=models.F("passport_issue_date")),
                name="ck_kyc_poa_passport_expiry_after_issue",
            ),
        ]

    def clean(self):
        passport_doc_types = {
            POADocumentType.PASSPORT,
        }
        national_id_doc_types = {
            POADocumentType.NATIONAL_ID,
            POADocumentType.CNIC,
            POADocumentType.NICOP,
        }

        if self.document_type in passport_doc_types and not self.passport_number:
            raise ValidationError(
                {"passport_number": "Passport number is required for passport-based POA records."}
            )

        if self.document_type in national_id_doc_types and not self.national_id_number:
            raise ValidationError(
                {"national_id_number": "National ID number is required for ID-based POA records."}
            )

        # TODO(KYC-POA-001): Align required fields with final POADocumentType values
        # and document_rules service once upload rules are finalized.

    def __str__(self) -> str:
        return f"POA {self.person_name} ({self.document_type})"