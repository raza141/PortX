from django.db import models
from django.utils import timezone
from django.db.models import Q, F


class Mandate(models.Model):
    """
    px_mand_hdr: contract container
    investor -> mandate -> portfolio(s)
    mandate -> IPS versions
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

    class ReportingMode(models.TextChoices):
        MONTHLY = "M", "Monthly"
        QUARTERLY = "Q", "Quarterly"
        ANNUALLY = "A", "Annually"

    class ReportingDeliveryMode(models.TextChoices):
        EMAIL = "E", "Email"
        TEXT = "T", "Text"
        PUSH_NOTICE = "P", "PUSH_NOTICE"
        WHATSAPP = "W", "Whatsapp"
        OTHER = "O", "Other"


    mand_id = models.BigAutoField(primary_key=True, db_column="mand_id", help_text="Mandate key, e.g. 3001")

    investor = models.ForeignKey(
        "crm.Investor",
        on_delete=models.PROTECT,
        related_name="mandates",
        db_column="inv_id",
        help_text="Owning investor, e.g. INV_000123",
    )

    mand_cd = models.CharField(max_length=24, unique=True, db_index=True, db_column="mand_cd",
                               help_text="Mandate code, e.g. MAND_BAL_001"
    )
    mand_nm = models.CharField(max_length=140, db_column="mand_nm",
                               help_text="Mandate name, e.g. Family Balanced",
    )

    base_ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="mandates",
        db_column="base_ccy_id",
        help_text="Mandate base currency, e.g. USD",
    )

    auth_cd = models.CharField(max_length=3, choices=Authority.choices, db_column="auth_cd",
                               default=Authority.SIGNAL_ONLY,
                               help_text="Authority, e.g. DIS"
    )
    aprv_md_cd = models.CharField(max_length=3, choices=ApprovalMode.choices,
                                  default=ApprovalMode.PRE_TRADE,
                                  db_column="aprv_md_cd", help_text="Approval mode, e.g. PRE")

    sts_cd = models.CharField(max_length=3, choices=Status.choices, default=Status.ACTIVE,
                              db_column="sts_cd", help_text="Status, e.g. ACT")

    incp_dt = models.DateField(default=timezone.localdate, db_column="incp_dt",
                               help_text="Mandate start date, e.g. 2026-02-09")
    term_dt = models.DateField(null=True, blank=True, db_column="term_dt",
                               help_text="Mandate end date, e.g. 2027-12-31")
    sign_dt = models.DateField(null=True, blank=True, db_column="sign_dt",
                               help_text="Signed date, e.g. 2026-02-10")

    bmk = models.ForeignKey(
        "masters.Benchmark",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="mandates",
        db_column="bmk_id",
        help_text="Default benchmark, e.g. MSCI World",
    )
    fee_sched = models.ForeignKey(
        "masters.FeeSchedule",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="mandates",
        db_column="fee_sched_id",
        help_text="Default fee schedule, e.g. 1% mgmt",
    )

    rpt_freq_txt = models.CharField(max_length=3,
                                    choices=ReportingMode.choices,
                                    default=ReportingMode.QUARTERLY,
                                    help_text="ReportingMode, e.g. QUARTERLY"
    )
    rpt_dlvr_txt = models.CharField(max_length=3,
                                    choices=ReportingDeliveryMode.choices,
                                    default=ReportingDeliveryMode.EMAIL, db_column="rpt_dlvr_txt",
                                    help_text="Reporting delivery, e.g. Email PDF"
    )

    act_ips_ver = models.ForeignKey(
        "policies.IPSVersion",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="+",
        db_column="act_ips_ver_id",
        help_text="Current IPS version pointer, e.g. ips_ver_id=9001",
    )

    doc_id = models.BigIntegerField(null=True, blank=True, db_column="doc_id",
                                    help_text="Signed mandate doc id, e.g. 555001")

    created_by = models.IntegerField(default=101, db_column="created_by", help_text="User id, e.g. 101")
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at", help_text="Created timestamp")
    updated_at = models.DateTimeField(auto_now=True, db_column="updated_at", help_text="Updated timestamp")

    class Meta:
        db_table = "px_mand_hdr"
        indexes = [
            models.Index(fields=["investor", "sts_cd"], name="ix_mand_inv_sts"),
            models.Index(fields=["mand_cd"], name="ix_mand_cd"),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(term_dt__isnull=True) | Q(term_dt__gt=F("incp_dt")),
                name="ck_mand_dt_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.mand_nm} ({self.mand_cd})"


