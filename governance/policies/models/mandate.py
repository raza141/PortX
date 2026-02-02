from django.db import models
from django.db.models import Q, F
from django.utils import timezone

from refdata.masters.models.currency import Currency

class Mandate(models.Model):
    """
    px_mand_hdr: mandate header (institutional agreement container)
    investor -> mandate -> portfolio(s)
    mandate -> ips versions
    """

    class Status(models.TextChoices):
        ACTIVE = "ACT", "Active"
        INACTIVE = "INA", "Inactive"

    class Authority(models.TextChoices):
        DISCRETIONARY = "DIS", "Discretionary"
        ADVISORY = "ADV", "Advisory"
        MODEL_ONLY = "MOD", "Model-only"
        SIGNAL_ONLY = "SIG", "Signal-only"

    class ApprovalMode(models.TextChoices):
        PRE_TRADE = "PRE", "Pre-trade approval"
        POST_TRADE_ACK = "PST", "Post-trade acknowledgement"
        NONE = "NON", "None"

    mandate_id = models.BigAutoField(primary_key=True, db_column="mand_id")

    investor = models.ForeignKey(
        "crm.Investor",
        on_delete=models.PROTECT,
        related_name="mandates",
        db_column="inv_id",
    )

    # Optional: relationship manager
    rm = models.ForeignKey(
        "crm.RM",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mandates",
        db_column="rm_id",
    )

    mandate_name = models.CharField(max_length=140, db_column="mand_nm")
    #FK here from from refdata.masters.models.currency import Currency
    # base_ccy = models.CharField(max_length=3, default="USD", db_column="base_ccy")
    base_ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="mandates",
        db_column="base_ccy_id",  # DB column name
        default="USD",  # only works if Currency PK is "USD" (usually it isn't)
    )

    authority = models.CharField(max_length=3, choices=Authority.choices, db_column="auth_cd")
    approval_mode = models.CharField(
        max_length=3, choices=ApprovalMode.choices, default=ApprovalMode.PRE_TRADE, db_column="aprv_md_cd"
    )

    status = models.CharField(max_length=3, choices=Status.choices, default=Status.ACTIVE, db_column="sts_cd")

    inception_dt = models.DateField(default=timezone.localdate, db_column="incp_dt")
    termination_dt = models.DateField(null=True, blank=True, db_column="term_dt")

    # Optional policy-level defaults (you can keep null in V1)
    benchmark = models.ForeignKey(
        "masters.Benchmark",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mandates",
        db_column="bmk_id",
    )
    fee_schedule = models.ForeignKey(
        "masters.FeeSchedule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mandates",
        db_column="fee_sched_id",
    )

    # Reporting preferences (policy-level)
    reporting_frequency = models.CharField(max_length=20, null=True, blank=True, db_column="rpt_freq")
    reporting_delivery = models.CharField(max_length=20, null=True, blank=True, db_column="rpt_dlvr")

    # Audit (keeping consistent with your current style)
    created_by = models.IntegerField(default=101, db_column="crt_by")
    created_at = models.DateTimeField(auto_now_add=True, db_column="crt_ts")
    updated_at = models.DateTimeField(auto_now=True, db_column="upd_ts")

    class Meta:
        db_table = "px_mand_hdr"
        indexes = [
            models.Index(fields=["investor", "status"], name="ix_mand_inv_sts"),
            models.Index(fields=["authority", "status"], name="ix_mand_auth_sts"),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(termination_dt__isnull=True) | Q(termination_dt__gt=F("inception_dt")),
                name="ck_mand_dt_range",
            ),
        ]

    def __str__(self) -> str:
        return self.mandate_name
