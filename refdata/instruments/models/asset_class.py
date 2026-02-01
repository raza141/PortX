from django.db import models
from django.conf import settings

# from .base import TimeStampedModel
from refdata.instruments.models.base import TimeStampedModel

class AssetClass(TimeStampedModel):
    """
    Reference table: high-level asset class bucket used for:
    - IPS/asset allocation reporting
    - high-level exposure summaries
    - validation rules (e.g., allowed instruments)
    """

    class RiskBucket(models.TextChoices):
        LOW = "LOW", "Low"
        LOW_MED = "LOW_MED", "Low/Medium"
        MED = "MED", "Medium"
        HIGH = "HIGH", "High"
        VAR = "VAR", "Variable"

    asset_class_id = models.BigAutoField(primary_key=True)

    # Stable code used across the system (do NOT change once in production).
    # Examples: EQTY, FI, FUND, CASH, FX
    asset_class_code = models.CharField(max_length=16, unique=True, db_index=True)

    # Display name (can be changed without breaking references)
    asset_class_name = models.CharField(max_length=64)

    # Short institutional description (used in admin/help text)
    asset_class_description = models.TextField(blank=True, default="")

    # Coarse risk category used for dashboards (not a risk model)
    risk_bucket = models.CharField(max_length=16, choices=RiskBucket.choices)

    # Soft active flag (avoid deleting reference data)
    is_active = models.BooleanField(default=True, db_index=True)

    # Used for consistent UI ordering (menus, dropdowns, reports)
    sort_order = models.PositiveSmallIntegerField(default=0)

    # Who created the reference row (optional for MVP)
    # NOTE: If you want a hard default like 101, ensure a user with id=101 exists.
    created_by = models.IntegerField(default=101)

    class Meta:
        db_table = "ref_asset_class"
        verbose_name = "Asset Class"
        verbose_name_plural = "Asset Classes"
        ordering = ["sort_order", "asset_class_code"]
        constraints = [
            # Optional: enforce unique sort order when active (comment out if not needed)
            # models.UniqueConstraint(fields=["sort_order"], name="uq_asset_class_sort_order"),
        ]
        indexes = [
            models.Index(fields=["is_active", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.asset_class_code} - {self.asset_class_name}"
