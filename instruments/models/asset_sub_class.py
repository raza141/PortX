from django.db import models
from django.conf import settings

from .asset_class import AssetClass, TimeStampedModel


class AssetSubClass(TimeStampedModel):
    """
    Reference table: granular instrument subtype.

    Why institutions use this:
    - Controls behavior flags (coupon/maturity/underlying)
    - Determines which "terms table" applies later (Phase II):
        * EQUITY terms, FI terms, FUND terms, DERIV terms, etc.
    - Drives validation and reporting buckets.
    """

    class TermsFamily(models.TextChoices):
        # Processing / terms-engine family (used to choose Phase II terms table)
        CASH = "CASH", "Cash"
        EQUITY = "EQUITY", "Equity"
        FI = "FI", "Fixed Income"
        FUND = "FUND", "Fund/Collective"
        FX = "FX", "FX"
        DERIV = "DERIV", "Derivative"
        CRYPTO = "CRYPTO", "Crypto"
        CMDTY = "CMDTY", "Commodity"
        RE = "RE", "Real Estate"
        NONE = "NONE", "None"  # if no terms table needed (rare)

    class IncomeType(models.TextChoices):
        NONE = "NONE", "None"
        DIVIDEND = "DIVIDEND", "Dividend"
        COUPON = "COUPON", "Coupon/Profit"
        DISTRIBUTION = "DISTRIBUTION", "Distribution"

    sub_asset_class_id = models.BigAutoField(primary_key=True)

    # Stable code. Once in production, treat as immutable.
    # Examples: EQ_COMMON, FI_GOVT, ETF_EQUITY
    sub_asset_class_code = models.CharField(max_length=32, unique=True, db_index=True)

    # Human readable description shown in dropdowns/admin.
    sub_asset_class_description = models.CharField(max_length=255)

    # FK to AssetClass (DB should store integer id).
    asset_class = models.ForeignKey(
        AssetClass,
        on_delete=models.PROTECT,  # protect reference data (institution standard)
        related_name="sub_classes",
        db_index=True,
    )

    # Determines which terms table / processing logic applies later.
    terms_family = models.CharField(max_length=16, choices=TermsFamily.choices)

    # Allows fractional quantity (ETFs, funds, FX, crypto, sometimes bonds via platforms).
    supports_fractional = models.BooleanField(default=False)

    # Cashflow / income nature (helps reporting and later corporate-actions logic).
    income_type = models.CharField(max_length=16, choices=IncomeType.choices, default=IncomeType.NONE)

    # Behavior flags used for validation + future valuation logic.
    requires_coupon = models.BooleanField(default=False)      # FI coupon/profit required?
    requires_maturity = models.BooleanField(default=False)    # maturity date required?
    requires_underlying = models.BooleanField(default=False)  # options, convertibles, swaps, etc.

    # True for funds/ETFs/collectives where holdings are basket-based
    is_collective = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True, db_index=True)

    # Ordering within an asset class dropdown (institution UI convention)
    sort_order = models.PositiveSmallIntegerField(default=0)

    created_by = models.IntegerField(default=101)

    class Meta:
        db_table = "ref_asset_sub_class"
        verbose_name = "Asset Sub Class"
        verbose_name_plural = "Asset Sub Classes"
        ordering = ["asset_class__sort_order", "sort_order", "sub_asset_class_code"]
        constraints = [
            # Sort order should be unique within an asset class (clean dropdown ordering)
            models.UniqueConstraint(
                fields=["asset_class", "sort_order"],
                name="uq_asset_sub_class_asset_class_sort_order",
            )
        ]
        indexes = [
            models.Index(fields=["asset_class", "is_active", "sort_order"]),
            models.Index(fields=["terms_family", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.sub_asset_class_code} ({self.asset_class.asset_class_code})"
