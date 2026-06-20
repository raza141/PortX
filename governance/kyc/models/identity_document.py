"""
governance/kyc/models/identity_document.py

Normalized identity documents. One mechanism serves the principal and joint
holders (null joint_holder = principal). Avoids fixed passport/CNIC columns and
supports multiple jurisdictions cleanly.
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from governance.kyc.choices import IdentityDocType
from governance.kyc.models.base import KYCAuditBase


class KYCIdentityDocument(KYCAuditBase):
    """An identity document belonging to the principal or a joint holder."""

    identity_document_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the identity document.",
    )
    application = models.ForeignKey(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="identity_documents",
        help_text="Application this identity document belongs to.",
    )
    joint_holder = models.ForeignKey(
        "kyc.KYCJointHolder",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="identity_documents",
        help_text="Owning joint holder; null means the document belongs to the principal.",
    )
    identity_doc_type = models.CharField(
        max_length=16,
        choices=IdentityDocType.choices,
        help_text="Type of identity document (passport, CNIC, Emirates ID, etc.).",
    )
    document_number = models.CharField(
        max_length=80,
        help_text="Document number as printed on the ID.",
    )
    issue_date = models.DateField(
        null=True, blank=True, help_text="Document issue date."
    )
    expiry_date = models.DateField(
        null=True, blank=True, help_text="Document expiry date (used for validity checks)."
    )
    issuing_country = models.ForeignKey(
        "masters.Country",
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="kyc_identity_documents",
        help_text="Country that issued the document (FK to reference country).",
    )

    class Meta:
        db_table = "px_kyc_identity_document"
        verbose_name = "KYC Identity Document"
        verbose_name_plural = "KYC Identity Documents"
        indexes = [
            models.Index(fields=["application", "identity_doc_type"], name="ix_kyc_iddoc_app_type"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(issue_date__isnull=True) | Q(expiry_date__isnull=True) | Q(expiry_date__gte=models.F("issue_date")),
                name="ck_kyc_iddoc_expiry_after_issue",
            ),
        ]

    def clean(self):
        if self.joint_holder_id and self.joint_holder.application_id != self.application_id:
            raise ValidationError(
                {"joint_holder": "Joint holder must belong to the same application."}
            )

        # TODO(KYC-IDDOC-001): Add document-type-specific validation rules
        # (e.g. mandatory expiry for passport, format rules by jurisdiction, uniqueness policy).

    def __str__(self) -> str:
        owner = f"JH#{self.joint_holder_id}" if self.joint_holder_id else "principal"
        return f"{self.identity_doc_type}:{self.document_number} ({owner})"