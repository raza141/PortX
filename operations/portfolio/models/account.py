from django.db import models
from django.utils import timezone
from django.db.models import Q, F


class Account(models.Model):
    """
    px_acct_hdr: custody/broker account (belongs to investor)
    """

    class AccountType(models.TextChoices):
        BROKERAGE = "BRK", "Brokerage"
        CUSTODY = "CUS", "Custody"
        CASH = "CSH", "Cash"
        MARGIN = "MRG", "Margin"
        PLATFORM = "PLT", "Platform"

    class Status(models.TextChoices):
        OPEN = "OPN", "Open"
        CLOSED = "CLS", "Closed"
        SUSPENDED = "SUS", "Suspended"
        RESTRICTED = "RST", "Restricted"

    acct_id = models.BigAutoField(primary_key=True, db_column="acct_id", help_text="Account key, e.g. 8001")

    investor = models.ForeignKey(
        "crm.Investor",
        on_delete=models.CASCADE,
        related_name="accounts",
        db_column="inv_id",
        help_text="Account owner investor, e.g. INV_000123",
    )

    broker = models.ForeignKey(
        "masters.Broker",
        on_delete=models.PROTECT,
        related_name="accounts",
        db_column="broker_id",
        help_text="Broker ref, e.g. IBKR",
    )

    acct_cd = models.CharField(max_length=60, db_index=True, db_column="acct_cd",
                               blank=True,
                               help_text="Broker account code, e.g. U1234567"
    )

    acct_tp_cd = models.CharField(max_length=3, choices=AccountType.choices, default=AccountType.BROKERAGE,
                                  db_column="acct_tp_cd", help_text="Account type, e.g. BRK")

    ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="accounts",
        null=True, blank=True,
        db_column="ccy_id",
        help_text="Account currency, e.g. AED",
    )

    sts_cd = models.CharField(max_length=3, choices=Status.choices, default=Status.OPEN,
                              db_column="sts_cd", help_text="Account status, e.g. OPN")

    opn_dt = models.DateField(null=True, blank=True, db_column="opn_dt", help_text="Opened date, e.g. 2026-02-01")
    cls_dt = models.DateField(null=True, blank=True, db_column="cls_dt", help_text="Closed date, e.g. 2027-06-30")

    created_by = models.IntegerField(default=101, db_column="created_by", help_text="User id, e.g. 101")
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at", help_text="Created timestamp")
    updated_at = models.DateTimeField(auto_now=True, db_column="updated_at", help_text="Updated timestamp")

    class Meta:
        db_table = "px_acct_hdr"
        constraints = [
            models.UniqueConstraint(fields=["broker", "acct_cd"], name="uq_acct_broker_cd"),
        ]
        indexes = [
            models.Index(fields=["investor", "sts_cd"], name="ix_acct_inv_sts"),
            models.Index(fields=["broker"], name="ix_acct_broker"),
        ]

    def __str__(self):
        return self.acct_cd
