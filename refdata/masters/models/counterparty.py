from django.db import models

from refdata.masters.choices import CounterpartyStatus, CounterpartyType
from refdata.masters.models.country import Country


class Counterparty(models.Model):
    counterparty_id = models.BigAutoField(primary_key=True)

    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Canonical short code.",
    )
    name = models.CharField(
        max_length=150,
        help_text="Counterparty display name.",
    )
    legal_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Registered legal name.",
    )

    counterparty_type = models.CharField(
        max_length=20,
        choices=CounterpartyType.choices,
        help_text="Bank, broker-dealer, custodian, OTC dealer, or other.",
    )

    country = models.ForeignKey(
        Country,
        db_column="country_id",
        to_field="country_id",
        on_delete=models.DO_NOTHING,
        related_name="counterparties",
        db_constraint=False,
        null=True,
        blank=True,
    )

    lei = models.CharField(max_length=20, null=True, blank=True)
    swift_bic = models.CharField(max_length=11, null=True, blank=True)

    status = models.CharField(
        max_length=3,
        choices=CounterpartyStatus.choices,
        default=CounterpartyStatus.ACTIVE,
    )

    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "counterparty"

    def __str__(self):
        return f"{self.code} - {self.name}"