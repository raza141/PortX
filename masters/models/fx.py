from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

from .currency import Currency

class FxRateDaily(models.Model):
    """
    Daily FX rates for supported pairs.
    mid = quote per 1 base (consistent with CurrencyPair).
    """
    fx_rate_daily_id = models.BigAutoField(primary_key=True)

    rate_date = models.DateField()

    base_currency = models.ForeignKey(
        Currency,
        db_column="base_currency_id",
        on_delete=models.PROTECT,
        related_name="fx_rates_as_base",
    )
    quote_currency = models.ForeignKey(
        Currency,
        db_column="quote_currency_id",
        on_delete=models.PROTECT,
        related_name="fx_rates_as_quote",
    )

    mid = models.DecimalField(
        max_digits=18,
        decimal_places=8,
        validators=[MinValueValidator(0)],
    )

    source = models.TextField(null=True, blank=True)         # e.g., "PSX", "ECB", "Broker"
    source_series = models.TextField(null=True, blank=True)  # e.g., "CLOSE", "FIXING"
    loaded_at = models.DateTimeField(null=True, blank=True)

    created_by = models.IntegerField(default=101)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "fx"
        indexes = [
            models.Index(fields=["rate_date"]),
            models.Index(fields=["base_currency", "quote_currency", "rate_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["rate_date", "base_currency", "quote_currency", "source_series"],
                name="uq_fx_rate_daily_pair_date_series",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.rate_date} {self.base_currency.code}/{self.quote_currency.code} {self.mid}"