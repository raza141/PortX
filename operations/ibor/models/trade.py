from django.db import models
from django.utils import timezone


class IborTrade(models.Model):
    """
    IBOR Trade Blotter (book of record for executed trades).
    Source can be MANUAL today; OMS/VENUE later will feed the same table.
    """

    class Side(models.TextChoices):
        BUY = "B", "Buy"
        SELL = "S", "Sell"

    class Status(models.TextChoices):
        BOOKED = "BOK", "Booked"
        CANCELLED = "CXL", "Cancelled"
        REVERSED = "REV", "Reversed"  # cancellation with reversal record
        PENDING = "PND", "Pending"    # optional if you want pre-book state later

    class Source(models.TextChoices):
        MANUAL = "MAN", "Manual"
        OMS = "OMS", "OMS"
        VENUE = "VEN", "Venue/API"
        IMPORT = "IMP", "Import"

    trd_id = models.BigAutoField(primary_key=True, db_column="trd_id")

    acct = models.ForeignKey(
        "portfolio.Account",
        on_delete=models.PROTECT,
        related_name="ibor_trades",
        db_column="acct_id",
        db_index=True,
        help_text="Booking account. All trades are booked at account level (institution standard).",
    )

    listing = models.ForeignKey(
        "instruments.SecurityListing",
        on_delete=models.PROTECT,
        related_name="ibor_trades",
        db_column="list_id",
        db_index=True,
        help_text="Tradable object (ticker+venue+currency). Trades link to listing, not the master instrument.",
    )

    side_cd = models.CharField(
        max_length=1,
        choices=Side.choices,
        db_column="side_cd",
        help_text="Trade side: B=Buy, S=Sell.",
    )

    qty = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        db_column="qty",
        help_text="Executed quantity. Use positive numbers; side indicates direction.",
    )

    px = models.DecimalField(
        max_digits=24,
        decimal_places=10,
        db_column="px",
        help_text="Executed price in listing price currency.",
    )

    trd_ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="ibor_trades",
        db_column="trd_ccy_id",
        help_text="Trade/price currency. Usually equals listing price currency; stored for audit/snapshot.",
    )

    trd_ts = models.DateTimeField(
        default=timezone.now,
        db_column="trd_ts",
        db_index=True,
        help_text="Execution timestamp (trade time).",
    )

    stl_dt = models.DateField(
        null=True,
        blank=True,
        db_column="stl_dt",
        db_index=True,
        help_text="Settlement/value date. Drives pending vs settled cash.",
    )

    gross_amt = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        db_column="gross_amt",
        null=True,
        blank=True,
        help_text="Gross consideration in trade currency. Optional if derived = qty*px.",
    )

    fees_amt = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=0,
        db_column="fees_amt",
        help_text="Total fees/commission in trade currency (positive number).",
    )

    tax_amt = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        default=0,
        db_column="tax_amt",
        help_text="Taxes/levies/withholding applied to this trade in trade currency.",
    )

    net_amt = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        null=True,
        blank=True,
        db_column="net_amt",
        help_text="Net cash impact in trade currency (buy is typically negative, sell positive). Optional if derived.",
    )

    ext_ref = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        db_column="ext_ref",
        help_text="External reference (broker exec id, venue trade id, import reference).",
    )

    src_cd = models.CharField(
        max_length=3,
        choices=Source.choices,
        default=Source.MANUAL,
        db_column="src_cd",
        db_index=True,
        help_text="Where this trade came from (manual/OMS/venue/import).",
    )

    sts_cd = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.BOOKED,
        db_column="sts_cd",
        db_index=True,
        help_text="Booking status (booked/cancelled/reversed).",
    )

    notes = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_column="notes",
        help_text="Free text notes for ops/audit.",
    )

    # audit
    crt_by = models.IntegerField(default=101, db_column="crt_by", help_text="Created by user id.")
    crt_ts = models.DateTimeField(auto_now_add=True, db_column="crt_ts", help_text="Create timestamp.")
    upd_ts = models.DateTimeField(auto_now=True, db_column="upd_ts", help_text="Update timestamp.")

    class Meta:
        db_table = "px_trd"
        verbose_name = "IBOR Trade"
        verbose_name_plural = "IBOR Trades"
        ordering = ["-trd_ts"]
        indexes = [
            models.Index(fields=["acct", "trd_ts"], name="ix_trd_acct_ts"),
            models.Index(fields=["listing", "trd_ts"], name="ix_trd_list_ts"),
            models.Index(fields=["sts_cd", "trd_ts"], name="ix_trd_sts_ts"),
        ]

    def __str__(self) -> str:
        return f"{self.trd_id} {self.side_cd} {self.qty}@{self.px}"
