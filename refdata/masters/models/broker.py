from django.db import models

# from .country import  Country

from refdata.masters.models.country import Country


class Broker(models.Model):
    class BrokerType(models.TextChoices):
        BROKER = "BRK", "Broker"
        CUSTODIAN = "CUS", "Custodian"
        PLATFORM = "PLT", "Platform"
        BANK = "BNK", "Bank"

    class Status(models.TextChoices):
        ACTIVE = "ACT", "Active"
        INACTIVE = "INA", "Inactive"

    broker_code = models.CharField(max_length=30, unique=True)  # e.g. SCS, SARWA, BMA
    broker_name = models.CharField(max_length=200)
    broker_type = models.CharField(max_length=3, choices=BrokerType.choices, default=BrokerType.BROKER)

    # Leave country as integer for now (later FK to Country model)
    country_id = models.ForeignKey(Country, db_column="country_id",
                                   null=True, blank=True, on_delete=models.SET_NULL, related_name="brokers"
                                   )

    default_base_currency = models.CharField(max_length=3, default="USD")
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=40, null=True, blank=True)
    regulator = models.CharField(max_length=80, null=True, blank=True)
    website = models.URLField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=3, choices=Status.choices, default=Status.ACTIVE)

    created_by = models.IntegerField(default=101)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "broker"
        indexes = [
            models.Index(fields=["broker_code"]),
            models.Index(fields=["status", "broker_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.broker_code} - {self.broker_name}"
