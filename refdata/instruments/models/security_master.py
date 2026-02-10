import uuid

from django.conf import settings
from django.db import models

from .asset_class import TimeStampedModel
from .asset_sub_class import AssetSubClass
from .issuer import Issuer


class SecurityMaster(TimeStampedModel):
    """
    Security Master (Instrument Master)

    One row = one instrument globally (e.g., PIBTL ordinary shares).
    - Does NOT represent "ticker" (that's SecurityListing).
    - Can have multiple listings across exchanges/currencies via SecurityListing.
    - Can have multiple identifiers (ISIN/CUSIP/FIGI/etc.) via SecurityIdentifier.

    This table is the backbone for:
    - transactions / holdings linkage
    - classification (asset sub-class, terms family)
    - issuer concentration reporting
    """

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"   # keep history; do not delete

    security_id = models.BigAutoField(primary_key=True)

    # Optional but strongly recommended for external integrations & stable references.
    security_uuid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
        help_text="Stable UUID for integrations (does not change).",
    )

    # Full instrument name for reports/admin screens.
    security_name = models.CharField(
        max_length=255,
        help_text="Instrument display name (e.g.,'Pakistan International Bulk Transportation - Ordinary Share').",
    )

    issuer = models.ForeignKey(
        Issuer,
        on_delete=models.PROTECT,
        related_name="securities",
        db_index=True,
        help_text="Issuer/legal entity that issued this instrument.",
    )

    sub_class = models.ForeignKey(
        AssetSubClass,
        on_delete=models.PROTECT,
        related_name="securities",
        db_index=True,
        help_text="Sub-asset class controlling terms family and validation flags.",
    )

    gics_sub_industry = models.ForeignKey(
        "taxonomy.GicsSubIndustry",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="securities",
        db_index=True,
        help_text="GICS sub-industry classification (security-level override; defaults from issuer mapping).",
    )

    # Optional: if not set, can be derived from issuer.country.py for MVP.
    domicile_country = models.ForeignKey(
        "masters.Country",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="domiciled_securities",
        help_text="Instrument domicile/registration country (nullable; often same as issuer country).",
    )

    # Economic/base currency of the instrument (not necessarily listing trading currency).
    base_currency = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="base_currency_securities",
        help_text="Economic/base currency (used for reporting/valuation conventions).",
    )

    # Convenience pointer for UI. Not required for correctness.
    # primary_listing = models.ForeignKey(
    #     "instruments.SecurityListing",
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name="primary_for_securities",
    #     help_text="Optional convenience link to the primary listing row.",
    # )

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )

    created_by = models.IntegerField(default=101)

    class Meta:
        db_table = "sec_security_master"
        verbose_name = "Security Master"
        verbose_name_plural = "Security Master"
        ordering = ["security_name"]
        indexes = [
            models.Index(fields=["status", "issuer"]),
            models.Index(fields=["status", "sub_class"]),
        ]
        constraints = [
            # Prevent duplicate instruments for same issuer + subclass + name (optional but helpful)
            models.UniqueConstraint(
                fields=["issuer", "sub_class", "security_name"],
                name="uq_security_master_issuer_subclass_name",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.security_name} ({self.sub_class.sub_asset_class_code})"
