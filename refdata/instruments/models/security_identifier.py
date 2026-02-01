from django.conf import settings
from django.db import models

from .asset_class import TimeStampedModel
from .security_listing import SecurityListing
from .security_master import SecurityMaster


class SecurityIdentifier(TimeStampedModel):
    """
    Security Identifier = external IDs used to match/import securities.

    Examples:
    - ISIN: security-level identifier (usually global)
    - CUSIP/SEDOL: security-level (often market-specific)
    - RIC: listing-level identifier (Reuters)
    - BBGID/FIGI: vendor identifiers used for data feeds

    This table enables:
    - importing broker.py statements reliably (ISIN beats ticker)
    - vendor market data mapping (Bloomberg/Refinitiv IDs)
    """

    class IdType(models.TextChoices):
        ISIN = "ISIN", "ISIN"
        CUSIP = "CUSIP", "CUSIP"
        SEDOL = "SEDOL", "SEDOL"
        FIGI = "FIGI", "FIGI"
        RIC = "RIC", "RIC (Refinitiv/Reuters)"
        BBGID = "BBGID", "Bloomberg Global ID"
        TICKER = "TICKER", "Ticker (venue-specific)"
        LOCAL_CODE = "LOCAL_CODE", "Local Exchange Code"
        FUND_TICKER = "FUND_TICKER", "Fund Ticker"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    security_identifier_id = models.BigAutoField(primary_key=True)

    security = models.ForeignKey(
        SecurityMaster,
        on_delete=models.CASCADE,
        related_name="identifiers",
        db_index=True,
    )

    # Nullable because many identifiers are security-level not listing-level.
    listing = models.ForeignKey(
        SecurityListing,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="identifiers",
        help_text="Optional: link identifier to a specific listing (RIC often listing-level).",
    )

    id_type = models.CharField(max_length=24, choices=IdType.choices, db_index=True)

    # The actual identifier string (e.g., PK000000PIBTL?).
    # Keep flexible length for vendor IDs.
    id_value = models.CharField(max_length=128, db_index=True)

    # Optional: where this came from (Manual, Bloomberg, Refinitiv, Broker statement).
    source_vendor = models.CharField(max_length=64, blank=True, default="")

    verified_at = models.DateField(
        null=True,
        blank=True,
        help_text="When this identifier was verified/confirmed (manual or vendor).",
    )

    is_primary = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Primary identifier of this type for the security.",
    )

    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    created_by = models.IntegerField(default=101)

    class Meta:
        db_table = "sec_security_identifier"
        verbose_name = "Security Identifier"
        verbose_name_plural = "Security Identifiers"
        ordering = ["security_id", "id_type", "id_value"]

        indexes = [
            models.Index(fields=["id_type", "id_value"]),
            models.Index(fields=["security", "id_type", "status"]),
        ]

        constraints = [
            # Global uniqueness per id_type + id_value (institution standard for clean mapping).
            # If you later face duplicates across markets, we can refine with listing_id.
            models.UniqueConstraint(
                fields=["id_type", "id_value"],
                name="uq_identifier_type_value",
            ),

            # Only one primary per security per id_type.
            models.UniqueConstraint(
                fields=["security", "id_type"],
                condition=models.Q(is_primary=True),
                name="uq_identifier_one_primary_per_security_type",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.id_type}:{self.id_value}"


