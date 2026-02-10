from django.db import models

class Benchmark(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACT", "Active"
        INACTIVE = "INA", "Inactive"

    class BenchmarkType(models.TextChoices):
        INDEX = "IDX", "Index"
        BLEND = "BLD", "Blend"
        ABSOLUTE = "ABS", "Absolute"
        CUSTOM = "CST", "Custom"

    class BenchmarkRole(models.TextChoices):
        MARKET = "MKT", "Market Benchmark"
        STYLE = "STY", "Style / Factor"
        SECTOR = "SEC", "Sector"
        FI = "FIR", "Fixed Income"
        INFL = "INF", "Inflation"
        ABS = "ABS", "Absolute Return"
        OTHER = "OTH", "Other"

    class Segment(models.TextChoices):
        BROAD = "BRD", "Broad Market"
        BLUECHIP = "BCH", "Blue-Chip"
        LARGECAP = "LCP", "Large-Cap"
        MIDCAP = "MCP", "Mid-Cap"
        SMALLCAP = "SCP", "Small-Cap"
        SHARIAH = "SHR", "Shariah"
        DIVIDEND = "DIV", "Dividend"
        VALUE = "VAL", "Value"
        GROWTH = "GRW", "Growth"

    class WeightingMethod(models.TextChoices):
        FF_MCAP = "FFM", "Free-float Market Cap"
        MCAP = "MCP", "Market Cap"
        PRICE = "PRC", "Price Weighted"
        EQUAL = "EQL", "Equal Weighted"
        FUND = "FND", "Fundamental Weighted"
        RISK = "RSK", "Risk Weighted"

    class ReturnType(models.TextChoices):
        PRICE_RETURN = "PR", "Price Return"
        TR_GROSS = "TRG", "Total Return (Gross)"
        TR_NET = "TRN", "Total Return (Net)"

    benchmark_type = models.CharField(max_length=3, choices=BenchmarkType.choices, default=BenchmarkType.INDEX,
                                      help_text="Benchmark type e.g. Index, Blend, Absolute"
                                      )
    benchmark_role = models.CharField(max_length=3, choices=BenchmarkRole.choices, default=BenchmarkRole.MARKET,
                                      help_text="Benchmark role e.g. Market, Fixed Income, Style"
                                      )
    segment = models.CharField(max_length=3, choices=Segment.choices, null=True, blank=True,
                               help_text="Benchmark segment e.g. Market, Fixed Income, Style"
                               )

    benchmark_name = models.CharField(max_length=120,
                                      help_text="Full Benchmark name e.g. KSE-100 Karachi 100-index")
    ticker = models.CharField(max_length=40, null=True, blank=True,
                              help_text="Ticker e.g. KSE-100 Karachi 100-index")
    provider = models.CharField(max_length=80, null=True, blank=True,
                                help_text="Provider e.g. KSE-100 Karachi 100-index")

    # currency should be FK  from masters.currency
    ccy_code = models.ForeignKey(
        "masters.Currency",
        to_field="code",
        db_column="code",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="benchmarks",
    )

    weighting_method = models.CharField(max_length=3, choices=WeightingMethod.choices, null=True, blank=True,
                                        help_text="Weighting method e.g. Price weighted, FF")
    return_type = models.CharField(max_length=3, choices=ReturnType.choices, default=ReturnType.PRICE_RETURN)

    methodology_url = models.URLField(null=True, blank=True,
                                      help_text="Methodology URL e.g. https://market.karachi.edu")

    status = models.CharField(max_length=3, choices=Status.choices, default=Status.ACTIVE,
                              help_text="Benchmark status e.g. Active")

    created_by = models.IntegerField(default=101)
    #djano ingestion auto_now works, however in raw-sql i need to set default now()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "benchmark"
        constraints = [
            models.UniqueConstraint(fields=["provider", "benchmark_name"], name="uq_bmk_provider_name"),
        ]
        indexes = [
            models.Index(fields=["benchmark_name"], name="ix_bmk_nm"),
            models.Index(fields=["ticker"], name="ix_bmk_tkr"),
            models.Index(fields=["provider"], name="ix_bmk_prov"),
            models.Index(fields=["benchmark_role"], name="ix_bmk_role"),
        ]

    def __str__(self) -> str:
        return f"{self.benchmark_name} ({self.ccy_code})"

