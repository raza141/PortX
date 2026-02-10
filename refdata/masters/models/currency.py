from django.db import models
from django.conf import settings


class Currency(models.Model):
    """
    Reference currency table (ISO-like).
    Example: USD, PKR, AED
    """
    currency_id = models.BigAutoField(primary_key=True, auto_created=True, verbose_name="ID")

    # increase length to handle the binance currencies (USDT and ETH)
    code = models.CharField(max_length=12, unique=True,
                            help_text="Currency code (e.g. USD, PKR, AED)"
                            )  # 'USD'
    numeric_code = models.PositiveIntegerField(null=True, blank=True,
                                               help_text="ISO 4217 numeric code for currency"
                                               )  # ISO 4217 numeric (optional)
    name = models.TextField(help_text="Currency Name")  # 'United States dollar'
    minor_units = models.PositiveSmallIntegerField(default=2)  # decimals: USD=2, JPY=0
    is_active = models.BooleanField(default=True)

    created_by = models.IntegerField(default=101)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ref_currency"
        ordering = ["currency_id"]

    def __str__(self) -> str:
        return self.code
