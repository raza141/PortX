# core/operations/ibor/models/trade.py
from __future__ import annotations

from django.db import models
from .common import IborTimeStampedModel, IborState


class IborSide(models.TextChoices):
    BUY = "BUY", "Buy"
    SELL = "SELL", "Sell"

class IborTradeEvent(IborTimeStampedModel):
    """
    Canonical trade event (broker-agnostic).

    This is the core 'TRD_EVT' for IBOR.
    - Created from manual entry OR from approved staged trades.
    - Must support versioning/corrections without deleting history.
    - State-driven truth levels (EXEC/CONF/SETTLED).
    """

    # Lineage & versioning
    source_system = models.CharField(
        max_length=40,
        help_text="Adapter/system identifier (e.g., 'psx_broker_x', 'sarwa', 'manual').",
    )
    external_ref = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Broker voucher/contract note id (should be stable for dedupe).",
    )
    version_no = models.PositiveIntegerField(
        default=1,
        help_text="Version number for the same external_ref (CORR creates a new version).",
    )
    replaces_trade = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replacement_trades",
        help_text="If this is a correction, points to the trade it replaces.",
    )

    # Who/where
    portfolio = models.ForeignKey(
        "portfolio.Portfolio",
        on_delete=models.PROTECT,
        related_name="ibor_trades",
        help_text="Portfolio owning the position (multi-base supported via portfolio.base_ccy).",
    )
    broker = models.ForeignKey(
        "masters.Broker",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_trades",
        help_text="Broker/counterparty executing or confirming the trade (optional in V1).",
    )
    exec_venue = models.ForeignKey(
        "masters.Exchange",   # or masters.ListingVenue if you have that
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_trades",
        help_text="Execution venue/exchange (PSX, NASDAQ, OTC venue). Optional; can default from instrument.",
    )

    # What (What came from instrument)
    instrument = models.ForeignKey(
        "instruments.SecurityListing",
        on_delete=models.PROTECT,
        related_name="ibor_trades",
        help_text="Instrument master key (map symbol/ISIN/ticker into this).",
    )
    asset_class = models.ForeignKey(
        "instruments.AssetClass",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_trades",
        help_text="Optional snapshot of asset class at trade time. Prefer deriving from instrument.",
    )
    asset_sub_class = models.ForeignKey(
        "instruments.AssetSubClass",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_trades",
        help_text="Optional snapshot of asset sub-class at trade time. Prefer deriving from instrument.",
    )

    side = models.CharField(
        max_length=4,
        choices=IborSide.choices,
        help_text="BUY or SELL.",
    )
    quantity = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Trade quantity (supports fractional shares).",
    )
    price = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Trade price per unit.",
    )
    # ✅ Currency should come from masters
    trade_ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="ibor_trade_ccy_trades",
        help_text="Trade/contract currency (ISO3 from masters).",
    )

    settle_ccy = models.ForeignKey(
        "masters.Currency",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="ibor_settle_ccy_trades",
        help_text="Settlement currency (optional; defaults to trade_ccy if null).",
    )

    trade_dt = models.DateField(
        help_text="Trade date (economic date).",
    )
    settle_dt = models.DateField(
        help_text="Settlement date (cash/security movement date).",
    )

    # Economics
    gross_amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Gross = quantity * price in trade_ccy (before charges).",
    )
    net_amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Net amount after charges (in settlement currency logic).",
    )

    # Lifecycle
    state_cd = models.CharField(
        max_length=10,
        choices=IborState.choices,
        default=IborState.EXEC,
        help_text="Lifecycle state for truth level selection (EXEC/CONF/SETTLED/CXL/CORR).",
    )
    state_ts = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when current state was achieved (optional).",
    )

    memo = models.TextField(
        blank=True,
        default="",
        help_text="Optional free-text notes (parsing notes, ops adjustments, etc.).",
    )

    class Meta:
        db_table = "ibor_trd_evt"
        indexes = [
            models.Index(fields=["portfolio", "trade_dt"]),
            models.Index(fields=["portfolio", "settle_dt"]),
            models.Index(fields=["instrument", "trade_dt"]),
            models.Index(fields=["state_cd", "trade_dt"]),
            models.Index(fields=["source_system", "external_ref", "version_no"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "external_ref", "version_no"],
                name="uq_ibor_trd_evt_src_ref_ver",
            )
        ]

    def __str__(self) -> str:
        return f"{self.portfolio_id}:{self.instrument_id}:{self.side} {self.quantity} @ {self.price} ({self.trade_dt})"


class IborChargeType(models.TextChoices):
    """
    Generic charge types. Use description for broker-specific labels.
    """
    COMM = "COMM", "Commission"
    TAX = "TAX", "Tax"
    LEVY = "LEVY", "Levy/Fee"
    VAT = "VAT", "VAT/GST/SST"
    STAMP = "STAMP", "Stamp duty"
    OTHER = "OTHER", "Other"


class IborChargeComponent(IborTimeStampedModel):
    """
    Charge component for a trade (flexible list).

    Examples
    --------
    - PSX Laga, SECP Laga, NCCPL, CDC, Adv Tax, SST
    - US SEC fee, FINRA fee
    - Platform fees on Sarwa
    """

    trade = models.ForeignKey(
        IborTradeEvent,
        on_delete=models.CASCADE,
        related_name="charges",
        help_text="Trade that this charge belongs to.",
    )
    charge_type_cd = models.CharField(
        max_length=10,
        choices=IborChargeType.choices,
        default=IborChargeType.OTHER,
        help_text="Normalized charge category (COMM/TAX/LEVY/VAT/etc.).",
    )
    description = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Broker label (e.g., 'PSX Laga', 'SST', 'SEC fee').",
    )
    rate = models.DecimalField(
        max_digits=18,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Optional rate (percent/bps) if available from source.",
    )
    amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Charge amount (positive number).",
    )
    currency = models.CharField(
        max_length=3,
        help_text="Charge currency ISO3.",
    )
    is_withholding = models.BooleanField(
        default=False,
        help_text="True if this is withholding tax (useful later for dividends/corporate actions).",
    )

    class Meta:
        db_table = "ibor_chg_cmp"
        indexes = [
            models.Index(fields=["trade"]),
            models.Index(fields=["charge_type_cd"]),
        ]

    def __str__(self) -> str:
        return f"{self.trade_id}:{self.charge_type_cd}:{self.amount} {self.currency}"


class IborTradeStateHistory(IborTimeStampedModel):
    """
    Optional: Keep a full timeline of state transitions for audit and replay.

    V1 can work without it (store only current state on trade),
    but this gives you future Gen3 / bi-temporal behavior without redesign.
    """

    trade = models.ForeignKey(
        IborTradeEvent,
        on_delete=models.CASCADE,
        related_name="state_history",
        help_text="Trade whose state changed.",
    )
    from_state = models.CharField(
        max_length=10,
        choices=IborState.choices,
        null=True,
        blank=True,
        help_text="Previous state (null if first state record).",
    )
    to_state = models.CharField(
        max_length=10,
        choices=IborState.choices,
        help_text="New state.",
    )
    transitioned_at = models.DateTimeField(
        help_text="Timestamp when the transition occurred.",
    )
    reason = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Reason (e.g., 'broker confirm received', 'settlement file matched').",
    )

    class Meta:
        db_table = "ibor_trd_state_hist"
        indexes = [
            models.Index(fields=["trade", "transitioned_at"]),
            models.Index(fields=["to_state"]),
        ]
