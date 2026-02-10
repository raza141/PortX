from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from .asset_class import TimeStampedModel
from .security_master import SecurityMaster


class SecurityListing(TimeStampedModel):
    """
    Security Listing = where/how an instrument trades.

    Example:
      - SecurityMaster: PIBTL Ordinary Share (instrument)
      - Listing: PIBTL on PSX in PKR (ticker/venue/exchange.py)

    Why institutions need it:
    - tickers can change over time (renames)
    - a security can be dual-listed on multiple exchanges
    - trading currency can differ by venue
    - you must preserve history (effective_from/to)
    """

    class VenueType(models.TextChoices):
        EXCHANGE = "EXCHANGE", "Exchange"
        OTC = "OTC", "OTC"
        PLATFORM = "PLATFORM", "Platform"  # e.g., Sarwa / internal platform routing
        INTERNAL = "INTERNAL", "Internal"  # synthetic lines if needed later

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        DELISTED = "DELISTED", "Delisted"

    security_listing_id = models.BigAutoField(primary_key=True,
                                              help_text="ID")

    security = models.ForeignKey(
        "instruments.SecurityMaster",
        on_delete=models.PROTECT,  # if instrument is removed in dev, listings go with it
        related_name="listings",
        db_index=True,
        help_text="Issuer ID e.g. PIBTL"
    )

    # NOTE: Replace "masters.Exchange" with your actual exchange.py model path
    exchange = models.ForeignKey(
        "masters.Exchange",
        null=True,
        blank=True,
        # models.PROTECT is used here
        on_delete=models.PROTECT,
        related_name="security_listings",
        help_text="Trading venue exchange.py (nullable for OTC/platform lines).",
    )

    # Ticker/symbol as used on that venue.
    ticker = models.CharField(
        max_length=32,
        db_index=True,
        validators=[RegexValidator(r"^[A-Za-z0-9\.\-_]+$", "Ticker contains invalid characters.")],
        help_text="Venue-specific ticker/symbol (e.g., PIBTL, IVV, 7010.SR).",
    )

    # Trading/price currency for this listing (can differ from instrument base currency).
    price_currency = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="listing_price_currencies",
        help_text="Currency in which this listing is traded/quoted.",
    )

    is_primary = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Primary listing used by default for UI/reporting (one per security ideally).",
    )

    venue_type = models.CharField(max_length=16, choices=VenueType.choices, default=VenueType.EXCHANGE)

    board_segment = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Board/segment (e.g., Main Board, OTCQX, etc.).",
    )

    effective_from = models.DateField(
        null=True,
        blank=True,
        help_text="Start date when this ticker/venue mapping became valid.",
    )

    effective_to = models.DateField(
        null=True,
        blank=True,
        help_text="End date when this listing ceased to be valid (delist/rename).",
    )

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    trading_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text="If false, block new trades for this listing (compliance/ops control).",
    )

    created_by = models.IntegerField(default=101)

    class Meta:
        db_table = "sec_security_listing"
        verbose_name = "Security Listing"
        verbose_name_plural = "Security Listings"
        ordering = ["security_id", "-is_primary", "ticker"]

        indexes = [
            models.Index(fields=["ticker", "status"]),
            models.Index(fields=["security", "is_primary", "status"]),
            models.Index(fields=["exchange", "ticker"]),
        ]

        constraints = [
            # Prevent duplicate active listings on the same exchange.py+ ticker for the same security.
            models.UniqueConstraint(
                fields=["security", "exchange", "ticker"],
                name="uq_listing_security_exchange_ticker",
            ),
            # Only one "primary" listing per security at a time (institution standard).
            models.UniqueConstraint(
                fields=["security"],
                condition=models.Q(is_primary=True),
                name="uq_listing_one_primary_per_security",
            ),
        ]

    def __str__(self) -> str:
        ex = self.exchange.exchange_code if self.exchange else self.venue_type
        return f"{self.ticker} @ {ex}"
