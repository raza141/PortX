from django.db import models
from django.utils import timezone
from django.db.models import Q, F

class IPSVersion(models.Model):
    """
    px_ips_ver: versioned IPS terms per mandate (V1)
    """

    class Status(models.TextChoices):
        DRAFT = "DRF", "Draft"
        ACTIVE = "ACT", "Active"
        SUPERSEDED = "SUP", "Superseded"
        INACTIVE = "INA", "Inactive"

    class RiskProfile(models.TextChoices):
        CONSERVATIVE = "CON", "Conservative"
        MODERATE = "MOD", "Moderate"
        AGGRESSIVE = "AGR", "Aggressive"

    class InvestmentObjective(models.TextChoices):
        PRESERVATION = "PRES", "Capital Preservation"
        INCOME = "INCM", "Income"
        GROWTH = "GRTH", "Growth"
        TOTAL_RETURN = "TRTN", "Total Return"

    class TimeHorizon(models.TextChoices):
        SHORT = "S", "Short"
        MEDIUM = "M", "Medium"
        LONG = "L", "Long"

    class LiquidityNeeds(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MED", "Medium"
        HIGH = "HIG", "High"

    class ReviewFrequency(models.TextChoices):
        MONTHLY = "MON", "Monthly"
        QUARTERLY = "QTR", "Quarterly"
        SEMI_ANNUAL = "SAA", "Semi-Annual"
        ANNUAL = "ANN", "Annual"
        ADHOC = "ADH", "Ad hoc"

    ips_ver_id = models.BigAutoField(primary_key=True, db_column="ips_ver_id",
                                     help_text="IPS version key, e.g. 9001")

    mandate = models.ForeignKey(
        "policies.Mandate",
        on_delete=models.CASCADE,
        related_name="ips_versions",
        db_column="mand_id",
        help_text="Parent mandate, e.g. MAND_BAL_001",
    )

    ver_no = models.PositiveIntegerField(db_column="ver_no", help_text="Version number, e.g. 1")
    ips_nm = models.CharField(max_length=140, db_column="ips_nm", help_text="IPS name, e.g. Balanced IPS v1")

    sts_cd = models.CharField(max_length=3, choices=Status.choices, default=Status.DRAFT,
                              db_column="sts_cd", help_text="Status, e.g. DRF")

    risk_prf_cd = models.CharField(max_length=3, choices=RiskProfile.choices, db_column="risk_prf_cd",
                                   help_text="Risk profile, e.g. MOD")
    inv_obj_cd = models.CharField(max_length=4, choices=InvestmentObjective.choices, db_column="inv_obj_cd",
                                  help_text="Objective, e.g. TRTN")
    tm_hzn_cd = models.CharField(max_length=1, choices=TimeHorizon.choices, db_column="tm_hzn_cd",
                                 help_text="Time horizon, e.g. L")
    liq_need_cd = models.CharField(max_length=3, choices=LiquidityNeeds.choices, db_column="liq_need_cd",
                                   help_text="Liquidity needs, e.g. MED")

    tgt_ret = models.DecimalField(max_digits=9, decimal_places=4, null=True, blank=True, db_column="tgt_ret",
                                  help_text="Target return, e.g. 0.0800")
    vol_cap = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True, db_column="vol_cap",
                                  help_text="Volatility cap, e.g. 0.1500")
    issuer_max = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True, db_column="iss_max",
                                     help_text="Issuer max weight, e.g. 0.0500")

    eff_fr_dt = models.DateField(default=timezone.localdate, db_column="eff_fr_dt",
                                 help_text="Effective from date, e.g. 2026-02-09")
    eff_to_dt = models.DateField(null=True, blank=True, db_column="eff_to_dt",
                                 help_text="Effective to date, e.g. 2027-02-08")

    rvw_freq_cd = models.CharField(max_length=3, choices=ReviewFrequency.choices, null=True, blank=True,
                                   db_column="rvw_freq_cd", help_text="Review frequency, e.g. QTR")
    nxt_rvw_due_dt = models.DateField(null=True, blank=True, db_column="nxt_rvw_due_dt",
                                      help_text="Next review due date, e.g. 2026-05-31")

    is_curr = models.BooleanField(default=False, db_column="is_curr",
                                  help_text="Current flag, e.g. True")
    chg_rsn = models.CharField(max_length=240, null=True, blank=True, db_column="chg_rsn",
                               help_text="Change reason, e.g. Updated risk limits")
    # This should be link to FK -----------------------------
    aprv_by = models.IntegerField(null=True, blank=True, db_column="aprv_by",
                                  help_text="Approver user id, e.g. 101")
    aprv_ts = models.DateTimeField(null=True, blank=True, db_column="aprv_ts",
                                   help_text="Approval timestamp")

    doc_id = models.BigIntegerField(null=True, blank=True, db_column="doc_id",
                                    help_text="Signed IPS doc id, e.g. 555101")

    crt_by = models.IntegerField(default=101, db_column="crt_by", help_text="Created by user id, e.g. 101")
    crt_ts = models.DateTimeField(auto_now_add=True, db_column="crt_ts", help_text="Created timestamp")
    upd_ts = models.DateTimeField(auto_now=True, db_column="upd_ts", help_text="Updated timestamp")

    class Meta:
        db_table = "px_ips_ver"
        indexes = [
            models.Index(fields=["mandate", "is_curr"], name="ix_ips_mand_curr"),
            models.Index(fields=["mandate", "eff_fr_dt"], name="ix_ips_mand_eff"),
            models.Index(fields=["sts_cd"], name="ix_ips_sts"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["mandate", "ver_no"], name="uq_ips_mand_verno"),
            models.UniqueConstraint(fields=["mandate"], condition=Q(is_curr=True), name="uq_ips_one_curr_per_mand"),
            models.CheckConstraint(
                check=Q(eff_to_dt__isnull=True) | Q(eff_to_dt__gt=F("eff_fr_dt")),
                name="ck_ips_eff_dt_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.ips_nm} v{self.ver_no}"
