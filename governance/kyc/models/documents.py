"""
governance/kyc/models/documents.py

Typed attachments with verification state. Uploads default to UNVERIFIED and are
rendered in the warning token until a reviewer verifies them.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from governance.kyc.choices import DocumentType, VerificationStatus
from governance.kyc.models.base import KYCAuditBase


def kyc_document_upload_path(instance, filename):
    """Per-application, date-partitioned upload path."""
    return f"kyc/documents/{instance.application_id}/{filename}"


class KYCDocument(KYCAuditBase):
    """An uploaded supporting document for a KYC application."""

    document_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the document.",
    )
    application = models.ForeignKey(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Application this document belongs to.",
    )
    joint_holder = models.ForeignKey(
        "kyc.KYCJointHolder",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="documents",
        help_text="Joint holder this document supports, when applicable.",
    )
    document_type = models.CharField(
        max_length=20,
        choices=DocumentType.choices,
        help_text="Category of the uploaded document.",
    )
    file = models.FileField(
        upload_to=kyc_document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png"])],
        help_text="The uploaded file. with extension only pdf, jpg, jpeg, png allowed.",
    )
    original_filename = models.CharField(
        max_length=255, null=True, blank=True, help_text="Original filename as uploaded."
    )
    verification_status = models.CharField(
        max_length=12,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED,
        help_text="Verification state; defaults to Unverified (warning token).",
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kyc_verified_documents",
        help_text="Reviewer who verified the document.",
    )
    verified_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp the document was verified."
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True, help_text="Timestamp the document was uploaded."
    )

    class Meta:
        db_table = "px_kyc_document"
        verbose_name = "KYC Document"
        verbose_name_plural = "KYC Documents"
        indexes = [
            models.Index(fields=["application", "document_type"], name="ix_kyc_doc_app_type"),
            models.Index(fields=["verification_status"], name="ix_kyc_doc_verif"),
        ]

    def clean(self):
        if self.joint_holder_id and self.joint_holder.application_id != self.application_id:
            raise ValidationError(
                {"joint_holder": "Joint holder must belong to the same application."}
            )

        if self.verification_status == VerificationStatus.VERIFIED:
            if not self.verified_by_id or not self.verified_at:
                raise ValidationError(
                    "Verified documents must have verified_by and verified_at."
                )

        if self.verification_status == VerificationStatus.UNVERIFIED:
            if self.verified_by_id or self.verified_at:
                raise ValidationError(
                    "Unverified documents cannot have verification metadata."
                )

        # TODO(KYC-DOC-001): Add content-type and file-size validation in upload service/form layer.
        # TODO(KYC-DOC-002): Consider UUID-based stored filenames to avoid collisions/leaking originals.

    def __str__(self) -> str:
        return f"{self.document_type} [{self.verification_status}]"