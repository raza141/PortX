from django.db import models


# Create your models here.
class Account(models.Model):
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

    investor = models.ForeignKey(
        "crm.Investor",
        on_delete=models.CASCADE,
        related_name="accounts"
    )

    broker = models.ForeignKey(
        "masters.Broker",
        on_delete=models.PROTECT,
        related_name="accounts"
    )

    # This is the real account code at the broker.py (SCS7663 / SWT613DC96 etc.)
    account_code_at_broker = models.CharField(max_length=60, null=False, blank=False)

    account_type = models.CharField(
        max_length=3,
        choices=AccountType.choices,
        default=AccountType.BROKERAGE
    )

    # Link currency to your existing masters.Currency table
    currency = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="accounts",
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.OPEN
    )

    opened_date = models.DateField(null=True, blank=True)
    closed_date = models.DateField(null=True, blank=True)

    # audit fields
    created_by = models.IntegerField(default=101)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "account"
        constraints = [
            # Prevent duplicate account code under the same broker.py
            models.UniqueConstraint(
                fields=["broker", "account_code_at_broker"],
                name="uq_account_broker_code"
            )
        ]
        indexes = [
            models.Index(fields=["investor", "status"]),
            models.Index(fields=["broker"]),
        ]

    def __str__(self):
        b = getattr(self.broker, "broker_code", "BROKER")
        return f"{b}:{self.account_code_at_broker}"

##===========END OF ACCOUNT MODEL ===========##