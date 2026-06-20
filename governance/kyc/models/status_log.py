"""
governance/kyc/models/status_log.py

Append-only workflow audit trail. Every status transition writes exactly one row
here via services/workflow.py. Rows are never updated or deleted. This model does
not extend KYCAuditBase: it has no updated_* columns by design (immutability).
"""
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

from governance.kyc.choices import ApplicationStatus, StatusAction


class KYCStatusLog(models.Model):
    """An immutable record of a single status transition."""

    status_log_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the status-log row.",
    )
    application = models.ForeignKey(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="status_logs",
        help_text="Application whose status changed.",
    )
    from_status = models.CharField(
        max_length=16,
        choices=ApplicationStatus.choices,
        null=True,
        blank=True,
        help_text="Status before the transition (null for the initial creation).",
    )
    to_status = models.CharField(
        max_length=16,
        choices=ApplicationStatus.choices,
        help_text="Status after the transition.",
    )
    action = models.CharField(
        max_length=16,
        choices=StatusAction.choices,
        help_text="The workflow action that caused the transition.",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="kyc_status_actions",
        help_text="User who performed the transition (audit).",
    )
    reason = models.TextField(
        null=True,
        blank=True,
        help_text="Reason/comment for the transition (e.g. info requested, rejection cause).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp the transition occurred (system-set).",
    )

    class Meta:
        db_table = "px_kyc_status_log"
        verbose_name = "KYC Status Log"
        verbose_name_plural = "KYC Status Logs"
        ordering = ["application", "created_at", "status_log_id"]
        indexes = [
            models.Index(fields=["application", "created_at"], name="ix_kyc_statuslog_app_ts"),
        ]
    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("KYCStatusLog rows are immutable and cannot be updated.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("KYCStatusLog rows are immutable and cannot be deleted.")

    def __str__(self) -> str:
        return f"{self.from_status}->{self.to_status} ({self.action})"