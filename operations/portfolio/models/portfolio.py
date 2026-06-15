# operations.portfolio.models.portfolio


from django.db import models
from django.utils import timezone
from django.db.models import Q, F
from operations.portfolio.models.account import Account


class Portfolio(models.Model):
    """
    px_port_hdr: investable book (rep/performance unit)
    """

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

    class PerfMethod(models.TextChoices):
        TWRR = "TWRR", "Time-weighted return"
        MWRR = "MWRR", "Money-weighted return"

    port_id = models.BigAutoField(primary_key=True, db_column="port_id", help_text="Portfolio key, e.g. 7001")
    port_cd = models.CharField(max_length=24, unique=True, db_index=True, db_column="port_cd",
                               help_text="Portfolio code, e.g. PORT_0001"
    )
    port_nm = models.CharField(max_length=120, db_column="port_nm",
                               help_text="Portfolio name, e.g. Balanced Book - Core"
    )

    mandate = models.ForeignKey(
        "policies.Mandate",
        on_delete=models.PROTECT,
        related_name="portfolios",
        db_column="mand_id",
        help_text="Parent mandate, e.g. MAND_BAL_001",
    )

    base_ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="portfolios",
        null=True, blank=True,
        db_column="base_ccy_id",
        help_text="Reporting currency, e.g. USD",
    )

    bmk = models.ForeignKey(
        "masters.Benchmark",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="portfolios",
        db_column="bmk_id",
        help_text="Portfolio benchmark, e.g. MSCI World",
    )

    fee_sched = models.ForeignKey(
        "masters.FeeSchedule",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name="portfolios",
        db_column="fee_sched_id",
        help_text="PF mgmt Fee schedule override, e.g. 1% mgmt",
    )

    perf_mthd_cd = models.CharField(max_length=4, choices=PerfMethod.choices, default=PerfMethod.TWRR,
                                    db_column="perf_mthd_cd", help_text="Perf method, e.g. TWRR")

    rebal_freq_cd = models.CharField(max_length=1, choices=Frequency.choices, default=Frequency.MONTHLY,
                                     db_column="rebal_freq_cd", help_text="Rebal freq, e.g. M")
    rpt_freq_cd = models.CharField(max_length=1, choices=Frequency.choices, default=Frequency.MONTHLY,
                                   db_column="rpt_freq_cd", help_text="Report freq, e.g. Q")
    rpt_dlvr_cd = models.CharField(max_length=3, choices=Delivery.choices, default=Delivery.EMAIL_PDF,
                                   db_column="rpt_dlvr_cd", help_text="Delivery, e.g. EML")

    trd_enbl_flg = models.BooleanField(default=False, db_column="trd_enbl_flg", help_text="Trading enabled, e.g. True")

    sts_cd = models.CharField(max_length=3, choices=Status.choices, default=Status.PENDING,
                              db_column="sts_cd", help_text="Status, e.g. PND")

    incp_dt = models.DateField(null=True, blank=True, db_column="incp_dt",
                               help_text="Portfolio inception, e.g. 2026-02-15")
    cls_dt = models.DateField(null=True, blank=True, db_column="cls_dt",
                              help_text="Portfolio close date, e.g. 2028-12-31")
    nxt_rvw_due_dt = models.DateField(null=True, blank=True, db_column="nxt_rvw_due_dt",
                                      help_text="Next review due date, e.g. 2026-05-31")

    created_by = models.IntegerField(default=101, db_column="created_by", help_text="User id, e.g. 101")
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at", help_text="Created timestamp")
    updated_at = models.DateTimeField(auto_now=True, db_column="updated_at", help_text="Updated timestamp")

    class Meta:
        db_table = "px_port_hdr"
        indexes = [
            models.Index(fields=["mandate", "sts_cd"], name="ix_port_mand_sts"),
            models.Index(fields=["sts_cd"], name="ix_port_sts"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["mandate", "port_nm"], name="uq_port_mand_nm"),
        ]

    def __str__(self):
        return f"{self.port_nm} ({self.port_cd})"

    @property
    def accounts(self):
        """
        Returns the accounts mapped to this portfolio.
        """
        from operations.portfolio.models.portfolio_account import PortfolioAccountMap
        account_ids = PortfolioAccountMap.objects.filter(portfolio=self).values_list('account_id', flat=True)
        return Account.objects.filter(pk__in=account_ids)
