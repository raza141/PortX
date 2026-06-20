# refdata/master/models/platform.py

from django.db import models

from refdata.masters.choices import PlatformStatus
from refdata.masters.models.country import Country


class Platform(models.Model):
    platform_id = models.BigAutoField(primary_key=True)

    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Canonical code, e.g. SARWA, ETORO, WAHDA.",
    )
    name = models.CharField(
        max_length=100,
        help_text="Platform display name.",
    )
    legal_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Registered legal entity or operator name.",
    )

    domicile_country = models.ForeignKey(
        "masters.Country",
        db_column="domicile_country_id",
        to_field="country_id",
        on_delete=models.DO_NOTHING,
        related_name="platforms_domiciled",
        db_constraint=False,
        null=True,
        blank=True,
        help_text="Country of incorporation or registration.",
    )

    operating_country = models.ForeignKey(
        "masters.Country",
        db_column="operating_country_id",
        to_field="country_id",
        on_delete=models.DO_NOTHING,
        related_name="platforms_operated",
        db_constraint=False,
        null=True,
        blank=True,
        help_text="Primary operating country, if different from domicile.",
    )

    regulator_name = models.CharField(max_length=100, null=True, blank=True,
                                      help_text="Regulator Name e.g. SECP, SEC, ADGM")
    license_ref = models.CharField(max_length=50, null=True, blank=True)
    website = models.URLField(null=True, blank=True)

    status = models.CharField(
        max_length=3,
        choices=PlatformStatus.choices,
        default=PlatformStatus.ACTIVE,
    )

    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "platform"

    def __str__(self):
        return f"{self.code} - {self.name}"