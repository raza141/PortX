"""
governance/kyc/models/base.py

Relational audit base for the KYC app. Deliberately does NOT reuse the legacy
IntegerField `AuditModel`: KYC requires real FK linkage to the acting user for
regulatory and operational auditability.
"""
from django.conf import settings
from django.db import models


class KYCAuditBase(models.Model):
    """Abstract base providing FK-linked created/updated audit columns."""

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_created",
        editable=False,
        help_text="User who created this record (FK to auth user, audit).",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_updated",
        null=True,
        blank=True,
        editable=False,
        help_text="User who last updated this record (FK to auth user, audit).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Timestamp this record was created (system-set).",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp this record was last updated (system-set).",
    )

    class Meta:
        abstract = True