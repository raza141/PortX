from django.db import models

# from .currency import Currency
from refdata.masters.models.currency import Currency

class CurrencyPair(models.Model):
    """
    Supported FX pairs (base/quote).
    Convention: rate = quote per 1 base (e.g., AED/PKR = 75 means 1 AED = 75 PKR)
    """
    currency_pair_id = models.BigAutoField(primary_key=True)

    base_currency = models.ForeignKey(
        Currency,
        db_column="base_currency_id",
        on_delete=models.PROTECT,
        related_name="pairs_as_base",
        help_text="Base currency e.g. USD"
    )
    quote_currency = models.ForeignKey(
        Currency,
        db_column="quote_currency_id",
        on_delete=models.PROTECT,
        related_name="pairs_as_quote",
        help_text="Quote currency e.g. Pkr"
    )

    # Optional convenience label (can be derived). Keep if you already have it.
    code = models.TextField(null=True, blank=True,
                            help_text="Currency code (e.g. USD/PKR)"
                            )  # e.g., "AED/PKR"

    is_active = models.BooleanField(default=True)

    created_by = models.IntegerField(default=101)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "currency_pair"
        constraints = [
            models.UniqueConstraint(
                fields=["base_currency", "quote_currency"],
                name="uq_currency_pair_base_quote",
            ),
            models.CheckConstraint(
                check=~models.Q(base_currency=models.F("quote_currency")),
                name="ck_currency_pair_base_ne_quote",
            ),
        ]

    def __str__(self) -> str:
        return self.code or f"{self.base_currency.code}/{self.quote_currency.code}"

