from django.db import models
from django.utils import timezone
from django.db.models import Q, F
from django.core.exceptions import ValidationError


class IPS(models.Model):
    """
    px_ips_hdr: IPS versions for a mandate.
    V1: keep portfolio NULL (mandate-level IPS only).
    V2+: allow portfolio override IPS (optional).
    """

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

    ips_id = models.BigAutoField(primary_key=True, db_column="ips_id")

    mandate = models.ForeignKey(
        "policies.Mandate",
        on_delete=models.PROTECT,
        related_name="ips_versions",
        db_column="mand_id",
    )

    # Optional: portfolio override (leave NULL in V1)
    portfolio = models.ForeignKey(
        "portfolio.Portfolio",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ips_overrides",
        db_column="port_id",
    )

    ips_name = models.CharField(max_length=140, db_column="ips_nm")
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

    is_current = models.BooleanField(default=True, db_column="is_curr")

    created_by = models.IntegerField(default=101, db_column="crt_by")
    created_at = models.DateTimeField(auto_now_add=True, db_column="crt_ts")
    updated_at = models.DateTimeField(auto_now=True, db_column="upd_ts")

    class Meta:
        db_table = "px_ips_hdr"
        indexes = [
            models.Index(fields=["mandate", "is_current"], name="ix_ips_mand_curr"),
            models.Index(fields=["portfolio", "is_current"], name="ix_ips_port_curr"),
            models.Index(fields=["status"], name="ix_ips_sts"),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(effective_end_dt__isnull=True) | Q(effective_end_dt__gt=F("effective_start_dt")),
                name="ck_ips_eff_dt_range",
            ),

            # One current mandate-level IPS per mandate (portfolio IS NULL)
            models.UniqueConstraint(
                fields=["mandate"],
                condition=Q(is_current=True, portfolio__isnull=True),
                name="uq_ips_one_curr_per_mand",
            ),

            # One current override IPS per portfolio (portfolio NOT NULL)
            models.UniqueConstraint(
                fields=["portfolio"],
                condition=Q(is_current=True, portfolio__isnull=False),
                name="uq_ips_one_curr_per_port",
            ),
        ]

    def clean(self):
        """
        If portfolio override is used later:
        enforce portfolio belongs to the same investor/mandate universe.
        We'll keep it minimal: only enforce mandate match if Portfolio has mandate_id in future.
        """
        if self.portfolio_id:
            port_mand_id = getattr(self.portfolio, "mandate_id", None)
            if port_mand_id is not None and port_mand_id != self.mandate_id:
                raise ValidationError("IPS mandate_id must match portfolio.mandate_id.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        scope = f"PORT:{self.portfolio_id}" if self.portfolio_id else "MAND"
        return f"{self.ips_name} [{scope}]"
