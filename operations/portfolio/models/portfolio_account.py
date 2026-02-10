from django.db import models
from django.utils import timezone
from django.db.models import Q, F


class PortfolioAccountMap(models.Model):
    """
    px_port_acct_map: links portfolios to accounts (M:N bridge)
    """

    class Role(models.TextChoices):
        PRIMARY = "PRI", "Primary"
        TRADING = "TRD", "Trading"
        CASH = "CSH", "Cash"
        CUSTODY = "CUS", "Custody"

    port_acct_map_id = models.BigAutoField(primary_key=True, db_column="port_acct_map_id",
                                           help_text="Mapping key, e.g. 9901")

    portfolio = models.ForeignKey(
        "portfolio.Portfolio",
        on_delete=models.CASCADE,
        related_name="account_links",
        db_column="port_id",
        help_text="Portfolio, e.g. PORT_0001",
    )

    account = models.ForeignKey(
        "portfolio.Account",
        on_delete=models.PROTECT,
        related_name="portfolio_links",
        db_column="acct_id",
        help_text="Account, e.g. U1234567",
    )

    role_cd = models.CharField(max_length=3, choices=Role.choices, default=Role.TRADING,
                               db_column="role_cd", help_text="Role, e.g. PRI")

    eff_fr_dt = models.DateField(default=timezone.localdate, db_column="eff_fr_dt",
                                 help_text="Effective from, e.g. 2026-02-09")
    eff_to_dt = models.DateField(null=True, blank=True, db_column="eff_to_dt",
                                 help_text="Effective to, e.g. 2027-01-01")

    is_primary_flg = models.BooleanField(default=False, db_column="is_primary_flg",
                                         help_text="Primary mapping flag, e.g. True")

    crt_by = models.IntegerField(default=101, db_column="crt_by", help_text="Created by user id, e.g. 101")
    crt_ts = models.DateTimeField(auto_now_add=True, db_column="crt_ts", help_text="Created timestamp")
    upd_ts = models.DateTimeField(auto_now=True, db_column="upd_ts", help_text="Updated timestamp")

    class Meta:
        db_table = "px_port_acct_map"
        indexes = [
            models.Index(fields=["portfolio"], name="ix_pam_port"),
            models.Index(fields=["account"], name="ix_pam_acct"),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(eff_to_dt__isnull=True) | Q(eff_to_dt__gt=F("eff_fr_dt")),
                name="ck_pam_eff_dt_range",
            ),
            models.UniqueConstraint(
                fields=["portfolio"],
                condition=Q(is_primary_flg=True),
                name="uq_pam_one_primary_per_port",
            ),
        ]

    def __str__(self):
        return f"{self.portfolio_id}<->{self.account_id}({self.role_cd})"
