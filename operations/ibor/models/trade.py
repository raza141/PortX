# ibor/models/trade.py
# This is like IborTradeEvent


from __future__ import annotations

from django.db import models

from .common import IborTimeStampedModel, IborState


class IborSide(models.TextChoices):
    BUY = "BUY", "Buy"
    SELL = "SELL", "Sell"


class IborBookStatus(models.TextChoices):
    NEW = "NEW", "New"
    BOOKED = "BOK", "Booked"
    ERROR = "ERR", "Error"
    REVERSED = "REV", "Reversed"


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


class IborTradeEvent(IborTimeStampedModel):
    """
    Canonical IBOR trade event (TRD_EVT).

    - Broker‑agnostic, portfolio‑centric record.
    - Supports versioning (CORR) via replaces_trade and version_no.
    - Lifecycle: EXEC / CONF / SETTLED / CXL / CORR.
    """

    # Lineage & versioning
    source_system = models.CharField(
        max_length=40,
        help_text="Adapter/system identifier (e.g. 'psx_broker_x', 'sarwa', 'manual').",
    )
    external_ref = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Broker/source trade id (voucher / contract note / execution id).",
    )
    version_no = models.PositiveIntegerField(
        default=1,
        help_text="Version number for same external_ref (CORR creates new version).",
    )
    replaces_trade = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="replacement_trades",
        help_text="If this is a correction, points to the trade it replaces.",
    )

    # Who / where
    portfolio = models.ForeignKey(
        "portfolio.Portfolio",
        on_delete=models.PROTECT,
        related_name="ibor_trades",
        help_text="Portfolio owning the position.",
    )
    account = models.ForeignKey(
        "portfolio.Account",
        on_delete=models.PROTECT,
        related_name="ibor_trades_ac",
        help_text="Account where the trade is initiated.",
    )
    # sleeve is removed for V1 will add back to V2
    broker = models.ForeignKey(
        "masters.Broker",
        on_delete=models.PROTECT,
        related_name="ibor_trades",
        help_text="Broker/counterparty executing or confirming the trade.",
    )
    exec_venue = models.ForeignKey(
        "masters.Exchange",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_trades",
        help_text="Execution venue/exchange (PSX, NASDAQ, OTC, etc.).",
    )

    # custodian also removed and will add back to v2

    # What
    instrument = models.ForeignKey(
        "instruments.SecurityListing",
        on_delete=models.PROTECT,
        related_name="ibor_trades",
        help_text="Listing-level security (e.g. BOP@PSX).",
    )
    asset_class = models.ForeignKey(
        "instruments.AssetClass",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_trades",
        help_text="Optional snapshot of asset class at trade time.",
    )
    asset_sub_class = models.ForeignKey(
        "instruments.AssetSubClass",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_trades",
        help_text="Optional snapshot of asset sub‑class at trade time.",
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

    trade_ccy = models.ForeignKey(
        "masters.Currency",
        null= True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="ibor_trade_ccy_trades",
        help_text="Trade/contract currency (ISO3 from masters).",
    )
    settle_ccy = models.ForeignKey(
        "masters.Currency",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="ibor_settle_ccy_trades",
        help_text="Settlement currency (defaults to trade_ccy if null).",
    )

    trade_dt = models.DateField(
        help_text="Trade date (economic date).",
    )
    settle_dt = models.DateField(
        help_text="Settlement date (cash/security movement date).",
    )

    # Front‑office / execution context
    order_type = models.CharField(
        max_length=30,
        blank=True,
        default="",
        help_text="Order type (e.g. Market, Limit).",
    )
    order_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Upstream OMS order id (if available).",
    )
    execution_id = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Execution/fill id from broker/OMS.",
    )
    trader = models.ForeignKey(
        "crm.RM",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_trades",
        help_text="RM / trader who placed this order.",
    )

    imported_flag = models.BooleanField(
        default=False,
        help_text="True if created via import/adapter instead of manual screen.",
    )
    manual_override = models.BooleanField(
        default=False,
        help_text="True if economics were manually overridden.",
    )
    override_reason = models.CharField(
        max_length=250,
        blank=True,
        default="",
        help_text="Reason for manual override (required when manual_override=True).",
    )
    fx_override_rate = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Optional FX override rate (trade_ccy -> settle_ccy).",
    )

    # Economics (derived by service)
    gross_amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Gross = quantity * price in trade_ccy (before charges).",
    )
    total_charges = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        default=0,
        help_text="Sum of all linked charge components (normalized into settle_ccy policy).",
    )
    net_amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Net amount after charges (settlement logic).",
    )
    settlement_cash_amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Cash that should move on settlement date in settle_ccy.",
    )

    # Lifecycle
    state_cd = models.CharField(
        max_length=10,
        choices=IborState.choices,
        default=IborState.EXEC,
        help_text="Lifecycle state (EXEC/CONF/SETTLED/CXL/CORR).",
    )
    state_ts = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when current state was achieved.",
    )
    book_sts_cd = models.CharField(
        max_length=3,
        choices=IborBookStatus.choices,
        default=IborBookStatus.NEW,
        db_index=True,
        help_text="Booking status: NEW/BOK/ERR/REV.",
    )
    book_ts = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When booking was completed (set by booking engine).",
    )
    book_err_txt = models.CharField(
        max_length=400,
        blank=True,
        default="",
        help_text="Booking error message if book_sts_cd=ERR.",
    )

    memo = models.TextField(
        blank=True,
        default="",
        help_text="Optional free‑text notes (ops commentary, parsing results, etc.).",
    )

    class Meta:
        db_table = "ibor_trd_evt"
        indexes = [
            models.Index(fields=["portfolio", "trade_dt"]),
            models.Index(fields=["portfolio", "settle_dt"]),
            models.Index(fields=["instrument", "trade_dt"]),
            models.Index(fields=["state_cd", "trade_dt"]),
            models.Index(fields=["source_system", "external_ref", "version_no"]),
            models.Index(fields=["broker", "trade_dt"]),
            models.Index(fields=["book_sts_cd", "trade_dt"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_system", "external_ref", "version_no"],
                name="uq_ibor_trd_evt_src_ref_ver",
            ),
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name="ck_ibor_trade_qty_gt_0",
            ),
            models.CheckConstraint(
                check=models.Q(price__gt=0),
                name="ck_ibor_trade_px_gt_0",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.portfolio_id}:{self.instrument_id}:{self.side} {self.quantity} @ {self.price} ({self.trade_dt})"


class IborChargeComponent(IborTimeStampedModel):
    """
    Flexible breakdown of commissions/taxes/fees per trade.
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
    cost_ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="ibor_trade_charge_ccy",
        help_text="Charge currency ISO3.",
    )
    is_withholding = models.BooleanField(
        default=False,
        help_text="True if this is withholding tax.",
    )
    override_flag = models.BooleanField(
        default=False,
        help_text="True if ops manually changed this charge.",
    )
    source_reference = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Optional source row id / code.",
    )

    class Meta:
        db_table = "ibor_chg_cmp"
        indexes = [
            models.Index(fields=["trade"]),
            models.Index(fields=["charge_type_cd"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount__gte=0),
                name="ck_ibor_charge_amt_gte_0",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.trade_id}:{self.charge_type_cd}:{self.amount} {self.cost_ccy_id}"


class IborTradeStateHistory(IborTimeStampedModel):
    """
    Timeline of state transitions for audit and replay.
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