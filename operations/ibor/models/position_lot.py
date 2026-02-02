from django.db import models


class PositionLot(models.Model):
    """
    FIFO lot tracking (V2/V1.5).
    For V1 you can leave empty table or add later.
    """

    lot_id = models.BigAutoField(primary_key=True, db_column="lot_id")

    acct = models.ForeignKey(
        "portfolio.Account",
        on_delete=models.PROTECT,
        related_name="position_lots",
        db_column="acct_id",
        db_index=True,
        help_text="Account that owns this lot.",
    )

    listing = models.ForeignKey(
        "instruments.SecurityListing",
        on_delete=models.PROTECT,
        related_name="position_lots",
        db_column="list_id",
        db_index=True,
        help_text="Listing this lot belongs to.",
    )

    open_qty = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        db_column="open_qty",
        help_text="Open quantity remaining in this lot.",
    )

    cost_ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="position_lots",
        db_column="cost_ccy_id",
        help_text="Currency of the lot cost basis (usually trade currency).",
    )

    unit_cost = models.DecimalField(
        max_digits=24,
        decimal_places=10,
        db_column="unit_cost",
        help_text="Unit cost (price) for this lot in cost_ccy.",
    )

    open_dt = models.DateField(
        db_column="open_dt",
        help_text="Lot open date (trade date).",
    )

    src_trd = models.ForeignKey(
        "ibor.IborTrade",
        on_delete=models.PROTECT,
        related_name="opened_lots",
        db_column="src_trd_id",
        help_text="Trade that opened this lot.",
    )

    # audit
    crt_by = models.IntegerField(default=101, db_column="crt_by", help_text="Created by user id.")
    crt_ts = models.DateTimeField(auto_now_add=True, db_column="crt_ts", help_text="Create timestamp.")
    upd_ts = models.DateTimeField(auto_now=True, db_column="upd_ts", help_text="Update timestamp.")

    class Meta:
        db_table = "px_pos_lot"
        verbose_name = "Position Lot"
        verbose_name_plural = "Position Lots"
        indexes = [
            models.Index(fields=["acct", "listing"], name="ix_lot_acct_list"),
        ]

    def __str__(self) -> str:
        return f"LOT {self.lot_id} {self.open_qty}"
