from django.db import models

# from .country import  Country

from refdata.masters.models.country import Country


class Broker(models.Model):
    class BrokerType(models.TextChoices):
        BROKER = "BRK", "Broker"
        CUSTODIAN = "CUS", "Custodian"
        PLATFORM = "PLT", "Platform"
        BANK = "BNK", "Bank"
        EXCHANGE = "EX", "Exchange"

    class Status(models.TextChoices):
        ACTIVE = "ACT", "Active"
        INACTIVE = "INA", "Inactive"

    broker_code = models.CharField(max_length=30, unique=True,
                                   help_text="Broker Code e.g. SCS")  # e.g. SCS, SARWA, BMA
    broker_name = models.CharField(max_length=200,
                                   help_text="Broker Full name"
                                   )
    broker_type = models.CharField(max_length=3, choices=BrokerType.choices, default=BrokerType.BROKER)

    # Leave country as integer for now (later FK to Country model)
    country_id = models.ForeignKey(Country, db_column="country_id",
                                   null=True, blank=True, on_delete=models.SET_NULL, related_name="brokers"
                                   )
    exchange = models.ForeignKey(
        "masters.Exchange",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="brokers",
        help_text="Primary exchange this broker is listed on."
    )

    default_base_currency = models.ForeignKey(
        "masters.Currency",
        related_name="default_base_currency",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Optional default currency for all currencies."
    )

    email = models.EmailField(null=True, blank=True,
                              help_text="Optional email address for this broker."
                              )
    phone = models.CharField(max_length=40, null=True, blank=True,
                             help_text="Optional phone number for this broker."
                             )
    regulator = models.CharField(max_length=80, null=True, blank=True,
                                 help_text="Optional regulator for this broker."
                                 )
    website = models.URLField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True,
                             help_text="Optional notes for this broker."
                             )

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
