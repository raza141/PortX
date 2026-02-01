
from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.utils import timezone


class PxAuditModel(models.Model):
    """
    Standard audit columns: crt_by/crt_ts/upd_ts (Bloomberg-ish)
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
        db_column="crt_by",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column="crt_ts")
    updated_at = models.DateTimeField(auto_now=True, db_column="upd_ts")

    class Meta:
        abstract = True


class IPS(PxAuditModel):
    class Status(models.TextChoices):
        DRAFT = "DRF", "Draft"
        ACTIVE = "ACT", "Active"
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

    # Anchor: IPS must belong to something real (Portfolio is simplest for V1)
    portfolio = models.ForeignKey(
        "portfolio.Portfolio",  # change app label if yours differs
        on_delete=models.PROTECT,
        related_name="ips_versions",
        db_column="port_id",
    )

    ips_name = models.CharField(max_length=120, db_column="ips_nm")
    status = models.CharField(max_length=3, choices=Status.choices, default=Status.DRAFT, db_column="sts_cd")

    risk_profile = models.CharField(max_length=3, choices=RiskProfile.choices, db_column="risk_prf_cd")
    investment_objective = models.CharField(max_length=4, choices=InvestmentObjective.choices, db_column="inv_obj_cd")
    time_horizon = models.CharField(max_length=1, choices=TimeHorizon.choices, db_column="tm_hzn_cd")
    liquidity_needs = models.CharField(max_length=3, choices=LiquidityNeeds.choices, db_column="liq_need_cd")

    effective_start_dt = models.DateField(default=timezone.localdate, db_column="eff_start_dt")
    effective_end_dt = models.DateField(null=True, blank=True, db_column="eff_end_dt")

    review_frequency = models.CharField(
        max_length=3, choices=ReviewFrequency.choices, null=True, blank=True, db_column="rvw_freq_cd"
    )
    next_review_due = models.DateField(null=True, blank=True, db_column="nxt_rvw_due_dt")

    # Versioning helper: exactly ONE current IPS per portfolio
    is_current = models.BooleanField(default=True, db_column="is_curr")

    # V2 hook (optional now, can stay null until you add constraints)
    # constraint_set = models.ForeignKey(
    #     "ConstraintSet",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="ips_links",
    #     db_column="cset_id",
    # )

    class Meta:
        db_table = "px_ips_hdr"
        indexes = [
            models.Index(fields=["portfolio", "status"], name="ix_ips_port_sts"),
            models.Index(fields=["portfolio", "is_current"], name="ix_ips_port_curr"),
        ]
        constraints = [
            # Postgres partial unique index: only one current IPS per portfolio
            models.UniqueConstraint(
                fields=["portfolio"],
                condition=Q(is_current=True),
                name="uq_ips_one_current_per_portfolio",
            ),
            # End date must be after start date (or null)
            models.CheckConstraint(
                check=Q(effective_end_dt__isnull=True) | Q(effective_end_dt__gt=F("effective_start_dt")),
                name="ck_ips_eff_dt_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.ips_name} ({self.get_status_display()})"