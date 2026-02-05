# core/operations/ibor/models/cash.py
from __future__ import annotations

from django.db import models
from .common import IborTimeStampedModel, IborState


class IborCashEventType(models.TextChoices):
    """
    Generic cash event types.
    """
    TRADE_SETTLE = "TRADE_SETTLE", "Trade settlement"
    TRADE_FEE = "TRADE_FEE", "Trade fee/charges"
    DEPOSIT = "DEPOSIT", "Deposit"
    WITHDRAW = "WITHDRAW", "Withdrawal"
    DIVIDEND = "DIVIDEND", "Dividend"
    TAX = "TAX", "Tax"
    FX_CONV = "FX_CONV", "FX conversion"
    OTHER = "OTHER", "Other"


class IborCashEvent(IborTimeStampedModel):
    """
    Canonical cash movement event.

    Ledger rules
    ------------
    - Use signed amounts consistently:
      +amount = cash inflow/credit
      -amount = cash outflow/debit

    Ladder rules
    ------------
    - effective_dt is the date the cash movement impacts availability (often settle_dt).
    """

    portfolio = models.ForeignKey(
        "portfolio.Portfolio",
        on_delete=models.PROTECT,
        related_name="ibor_cash_events",
        help_text="Portfolio whose cash is impacted.",
    )
    # ✅ Currency should come from masters
    currency = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="ibor_cash_ccy_trades",
        help_text="Trade/contract currency (ISO3 from masters).",
    )
    amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Signed cash amount: +inflow, -outflow.",
    )
    effective_dt = models.DateField(
        help_text="Date when cash movement is effective for cash ladder.",
    )
    cash_event_type = models.CharField(
        max_length=20,
        choices=IborCashEventType.choices,
        default=IborCashEventType.OTHER,
        help_text="Type/category of cash movement.",
    )

    # Linkage (optional)
    trade = models.ForeignKey(
        "ibor.IborTradeEvent",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cash_events",
        help_text="If cash event is caused by a trade settlement/fee, link to the trade.",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Free text description (broker label, reason, etc.).",
    )

    # Lifecycle (optional)
    state_cd = models.CharField(
        max_length=10,
        choices=IborState.choices,
        default=IborState.CONF,
        help_text="Lifecycle state of cash event (can mirror trade state).",
    )

    class Meta:
        db_table = "ibor_csh_evt"
        indexes = [
            models.Index(fields=["portfolio", "currency", "effective_dt"]),
            models.Index(fields=["cash_event_type", "effective_dt"]),
            models.Index(fields=["trade"]),
        ]

    def __str__(self) -> str:
        return f"{self.portfolio_id}:{self.currency}:{self.amount} @ {self.effective_dt}"
