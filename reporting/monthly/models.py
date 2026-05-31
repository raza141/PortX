from django.db import models


class ReportRequest(models.Model):
    """
    reporting_request: One record per monthly report generation request.
    Stores the PM's manual commentary inputs and tracks PDF generation + delivery.
    All financial data is computed on-the-run from IBOR tables — no duplication.
    """

    class Status(models.TextChoices):
        DRAFT     = "DRF", "Draft"
        GENERATED = "GEN", "Generated"
        SENT      = "SNT", "Sent"
        FAILED    = "FAL", "Failed"

    # ── Identity ──────────────────────────────────────────────
    rpt_req_id = models.BigAutoField(
        primary_key=True, db_column="rpt_req_id",
        help_text="Report request key, e.g. 1"
    )
    portfolio_id = models.BigIntegerField(
        db_column="portfolio_id", db_index=True,
        help_text="FK to px_port_hdr.port_id, e.g. 1"
    )
    period_end_dt = models.DateField(
        db_column="period_end_dt",
        help_text="Month-end date for this report, e.g. 2026-05-31"
    )

    # ── PM Inputs (only fields that require human judgment) ───
    market_commentary = models.TextField(
        blank=True, default="", db_column="market_commentary",
        help_text="PM market commentary for the month"
    )
    portfolio_commentary = models.TextField(
        blank=True, default="", db_column="portfolio_commentary",
        help_text="PM portfolio-specific commentary"
    )
    outlook = models.TextField(
        blank=True, default="", db_column="outlook",
        help_text="PM forward outlook and action plan"
    )

    # ── Status & Delivery ─────────────────────────────────────
    sts_cd = models.CharField(
        max_length=3, choices=Status.choices, default=Status.DRAFT,
        db_column="sts_cd", help_text="Report status, e.g. DRF"
    )
    pdf_path = models.CharField(
        max_length=512, blank=True, default="", db_column="pdf_path",
        help_text="Relative path to generated PDF, e.g. reports/2026-05/PORT_0001.pdf"
    )
    sent_to_email = models.EmailField(
        blank=True, default="", db_column="sent_to_email",
        help_text="Email address the report was delivered to"
    )
    generated_at = models.DateTimeField(
        null=True, blank=True, db_column="generated_at",
        help_text="Timestamp when PDF was successfully generated"
    )
    sent_at = models.DateTimeField(
        null=True, blank=True, db_column="sent_at",
        help_text="Timestamp of successful email delivery"
    )
    error_txt = models.TextField(
        blank=True, default="", db_column="error_txt",
        help_text="Error message if generation or delivery failed"
    )

    # ── Audit ─────────────────────────────────────────────────
    created_by = models.IntegerField(
        default=101, db_column="created_by",
        help_text="User id who triggered the report, e.g. 101"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, db_column="created_at",
        help_text="Created timestamp"
    )
    updated_at = models.DateTimeField(
        auto_now=True, db_column="updated_at",
        help_text="Updated timestamp"
    )

    class Meta:
        db_table = "reporting_request"
        unique_together = [("portfolio_id", "period_end_dt")]
        ordering = ["-period_end_dt"]
        indexes = [
            models.Index(fields=["portfolio_id", "period_end_dt"], name="ix_rpt_port_dt"),
            models.Index(fields=["sts_cd"],                         name="ix_rpt_sts"),
            models.Index(fields=["period_end_dt"],                  name="ix_rpt_dt"),
        ]

    def __str__(self) -> str:
        return (
            f"Report | port={self.portfolio_id} "
            f"| {self.period_end_dt} "
            f"| {self.get_sts_cd_display()}"
        )