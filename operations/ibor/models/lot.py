# core/operations/ibor/models/lot.py
from __future__ import annotations

from django.db import models
from .common import IborTimeStampedModel


class IborTaxLot(IborTimeStampedModel):
    """
    FIFO tax lot (inventory).

    Creation rule (engine, not model):
    - Create lot when BUY trade reaches CONF (or EXEC if you prefer faster, but CONF is safer).
    - Allocate charges into cost basis according to your policy (per-trade).

    This model stores the resulting lot inventory.
    """

    portfolio = models.ForeignKey(
        "portfolio.Portfolio",
        on_delete=models.PROTECT,
        related_name="ibor_lots",
        help_text="Portfolio owning this lot.",
    )
    instrument = models.ForeignKey(
        "instruments.SecurityListing",
        on_delete=models.PROTECT,
        related_name="ibor_lots",
        help_text="Instrument for this lot.",
    )
    acquired_dt = models.DateField(
        help_text="Acquisition date (usually trade_dt).",
    )
    trade = models.ForeignKey(
        "ibor.IborTradeEvent",
        on_delete=models.PROTECT,
        related_name="created_lots",
        help_text="BUY trade event that created this lot.",
    )

    open_qty = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Original lot quantity.",
    )
    remaining_qty = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Remaining lot quantity after FIFO consumptions.",
    )

    unit_cost = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Unit cost including allocated charges (in cost_ccy).",
    )
    cost_ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="ibor_lot_cost_ccy",
        help_text="Cost currency ISO3 (typically portfolio base or trade currency per policy).",
    )

    class Meta:
        db_table = "ibor_lot_inv"
        indexes = [
            models.Index(fields=["portfolio", "instrument", "acquired_dt"]),
            models.Index(fields=["instrument"]),
            models.Index(fields=["trade"]),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(open_qty__gt=0), name="ck_lot_open_qty_gt_0"),
            models.CheckConstraint(check=models.Q(remaining_qty__gte=0), name="ck_lot_rem_qty_gte_0"),
            models.CheckConstraint(check=models.Q(remaining_qty__lte=models.F("open_qty")), name="ck_lot_rem_le_open"),
        ]



class IborLotConsumption(IborTimeStampedModel):
    """
    Lot consumption record (FIFO).

    - Created when a SELL trade is processed by the FIFO engine.
    - One SELL trade may create multiple consumption rows (consuming multiple lots).
    """

    sell_trade = models.ForeignKey(
        "ibor.IborTradeEvent",
        on_delete=models.PROTECT,
        related_name="lot_consumptions",
        help_text="SELL trade that consumed lots.",
    )
    lot = models.ForeignKey(
        IborTaxLot,
        on_delete=models.PROTECT,
        related_name="consumptions",
        help_text="Lot that was consumed.",
    )
    consumed_qty = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Quantity consumed from this lot (FIFO).",
    )
    unit_cost = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Unit cost used for this consumption (copied from lot at time of consumption).",
    )
    cost_ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="lot_consumptions_currency",
        help_text="Currency of the cost basis.",
    )
    cost_basis = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Total cost basis consumed = consumed_qty * unit_cost.",
    )

    class Meta:
        db_table = "ibor_lot_cns"
        indexes = [
            models.Index(fields=["sell_trade"]),
            models.Index(fields=["lot"]),
        ]
        constraints = [
            models.CheckConstraint(check=models.Q(consumed_qty__gt=0), name="ck_lc_qty_gt_0"),
            models.UniqueConstraint(fields=["sell_trade", "lot"], name="uq_lot_cns_sell_lot"),
        ]
