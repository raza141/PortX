from django.db import models


class Portfolio(models.Model):
    # --- enums ---
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

    # --- keys / identifiers ---
    portfolio_id = models.BigAutoField(primary_key=True, db_column="port_id")
    portfolio_name = models.CharField(max_length=120, db_column="port_nm")

    # ✅ NEW: Portfolio belongs to Mandate (Investor implied by mandate)
    mandate = models.ForeignKey(
        "policies.Mandate",
        on_delete=models.PROTECT,
        related_name="portfolios",
        db_column="mand_id",
        null=False,
        blank=False,
    )

    # Optional (V2): portfolio-level IPS override (keep NULL in V1)
    ips_override = models.ForeignKey(
        "policies.IPS",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="portfolio_overrides",
        db_column="ips_ovr_id",
    )

    # base currency (reporting base; the book itself is multi-ccy later)
    base_currency = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="portfolios",
        null=True,
        blank=True,
        db_column="base_ccy_id",
    )

    benchmark = models.ForeignKey(
        "masters.Benchmark",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="portfolios",
        db_column="bmk_id",
    )

    fee_schedule = models.ForeignKey(
        "masters.FeeSchedule",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="portfolios",
        db_column="fee_sched_id",
    )

    # rebalancing/reporting preferences (can later move to mandate-level defaults)
    rebalancing_frequency = models.CharField(
        max_length=1,
        choices=Frequency.choices,
        default=Frequency.MONTHLY,
        db_column="rebal_freq_cd",
    )

    reporting_frequency = models.CharField(
        max_length=1,
        choices=Frequency.choices,
        default=Frequency.MONTHLY,
        db_column="rpt_freq_cd",
    )

    reporting_delivery = models.CharField(
        max_length=3,
        choices=Delivery.choices,
        default=Delivery.EMAIL_PDF,
        db_column="rpt_dlvr_cd",
    )

    trading_enabled = models.BooleanField(default=False, db_column="trd_enbl_flg")

    status = models.CharField(
        max_length=3,
        choices=Status.choices,
        default=Status.PENDING,
        db_column="sts_cd",
    )

    inception_date = models.DateField(null=True, blank=True, db_column="incp_dt")
    next_review_due = models.DateField(null=True, blank=True, db_column="nxt_rvw_due_dt")

    # optional convenience only (real linkage is via PortfolioAccountMap later)
    primary_account = models.ForeignKey(
        "portfolio.Account",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="primary_for_portfolios",
        db_column="prim_acct_id",
    )

    # audit
    created_by = models.IntegerField(default=101, db_column="crt_by")
    created_at = models.DateTimeField(auto_now_add=True, db_column="crt_ts")
    updated_at = models.DateTimeField(auto_now=True, db_column="upd_ts")

    class Meta:
        db_table = "px_port_hdr"
        indexes = [
            models.Index(fields=["mandate", "status"], name="ix_port_mand_sts"),
            models.Index(fields=["status"], name="ix_port_sts"),
        ]
        constraints = [
            # unique portfolio name per mandate (investor implied)
            models.UniqueConstraint(
                fields=["mandate", "portfolio_name"],
                name="uq_port_mand_nm",
            )
        ]

    def __str__(self):
        return self.portfolio_name
