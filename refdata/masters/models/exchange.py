from django.db import models

# from .country import Country
# from .currency import Currency

from refdata.masters.models.country import Country
from refdata.masters.models.currency import Currency

class Exchange(models.Model):
    class MarketStatus(models.TextChoices):
        ACTIVE = "ACT", "Active"
        INACTIVE = "INA", "Inactive"

    exchange_id = models.IntegerField(primary_key=True)
    country = models.ForeignKey(
        Country,
        db_column="country_id",
        to_field="country_id",
        on_delete=models.DO_NOTHING,
        related_name="exchanges",
        db_constraint=False,  # avoids Django trying to manage DB constraints
        null=True,
        blank=True,
    )
    exchange_name = models.CharField(max_length=100)
    exchange_code = models.CharField(max_length=20)
    mic = models.CharField(max_length=4, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    # FK to Currency model
    exchange_currency = models.ForeignKey(Currency,
        db_column="code",
        to_field="code",
        on_delete=models.DO_NOTHING,
        related_name="exchanges",
        db_constraint=False,
        null=True,
        blank=True,
    )
    market_status = models.CharField(choices=MarketStatus.choices, default=MarketStatus.ACTIVE, max_length=10)

    created_at = models.DateTimeField(null=True, blank=True)

    # Existing DB columns are country_id and currency_code


    class Meta:
        db_table = "exchange"   # because it is public.exchange in your screenshot

    def __str__(self):
        return f"{self.exchange_code} - {self.exchange_name}"

## ================= END OF Exchange ================== ##