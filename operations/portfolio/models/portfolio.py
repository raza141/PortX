from django.db import models


class Portfolio(models.Model):
    class MandateType(models.TextChoices):
        DISCRETIONARY = "DIS", "Discretionary"
        ADVISORY = "ADV", "Advisory"
        EXECUTION_ONLY = "EXO", "Execution-Only"

    class Status(models.TextChoices):
        ACTIVE = "ACT", "Active"
        PENDING = "PND", "Pending Onboarding"
        SUSPENDED = "SUS", "Suspended"
        CLOSED = "CLS", "Closed"

    class Frequency(models.TextChoices):
        DAILY = "D", "Daily"
        MONTHLY = "M", "Monthly"
        QUARTERLY = "Q", "Quarterly"
        SEMI_ANNUAL = "S", "Semi-Annual"
        ANNUAL = "A", "Annual"

    class Delivery(models.TextChoices):
        PORTAL = "PRT", "Portal"
        EMAIL_PDF = "EML", "Email PDF"
        WHATSAPP = "WAP", "WhatsApp"
        SMS = "SMS", "SMS"
        POST = "PST", "Post"

    portfolio_name = models.CharField(max_length=120)

    investor_id = models.ForeignKey(
        "crm.Investor",
        on_delete=models.CASCADE,
        related_name="portfolios"
    )

    base_currency = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="portfolios",
        null=True,
        blank=True
    )

    mandate_type = models.CharField(
        max_length=3,
        choices=MandateType.choices,
        default=MandateType.DISCRETIONARY
    )

    benchmark = models.ForeignKey(
        "masters.Benchmark",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="portfolios"
    )

    fee_schedule = models.ForeignKey(
        "masters.FeeSchedule",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="portfolios"
    )

    rebalancing_frequency = models.CharField(
        max_length=1,
        choices=Frequency.choices,
        default=Frequency.MONTHLY
    )

    reporting_frequency = models.CharField(
        max_length=1,
        choices=Frequency.choices,
        default=Frequency.MONTHLY
    )

    reporting_delivery = models.CharField(
        max_length=3,
        choices=Delivery.choices,
        default=Delivery.EMAIL_PDF
    )

    trading_enabled = models.BooleanField(default=False)

    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.PENDING
    )

    inception_date = models.DateField(null=True, blank=True)
    # Next review 
    next_review_due = models.DateField(null=True, blank=True)

    # optional: convenience only (real linkage is via PortfolioAccount)
    primary_account = models.ForeignKey(
        "portfolio.Account",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="primary_for_portfolios"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "portfolio"
        constraints = [
            models.UniqueConstraint(
                fields=["investor_id", "portfolio_name"],
                name="uq_portfolio_investor_name"
            )
        ]
        indexes = [
            models.Index(fields=["investor_id", "status"]),
        ]

    def __str__(self):
        return self.portfolio_name

##===========END OF PORTFOLIO MODEL ===========##