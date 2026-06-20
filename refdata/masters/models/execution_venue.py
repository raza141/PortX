
from django.core.exceptions import ValidationError
from django.db import models

from refdata.masters.choices import ExecutionVenueStatus, ExecutionVenueType


class ExecutionVenue(models.Model):
    execution_venue_id = models.BigAutoField(primary_key=True)

    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Canonical code, e.g. PSX, SARWA, JPM_OTC, XOFF.",
    )
    name = models.CharField(
        max_length=100,
        help_text="Display name of the execution venue.",
    )

    venue_type = models.CharField(
        max_length=20,
        choices=ExecutionVenueType.choices,
        help_text="Exchange, platform, counterparty, OTC, or internal.",
    )

    exchange = models.ForeignKey(
        "masters.Exchange",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="execution_venues",
    )
    platform = models.ForeignKey(
        "masters.Platform",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="execution_venues",
    )
    counterparty = models.ForeignKey(
        "masters.Counterparty",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="execution_venues",
    )

    status = models.CharField(
        max_length=3,
        choices=ExecutionVenueStatus.choices,
        default=ExecutionVenueStatus.ACTIVE,
    )

    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "execution_venue"
        constraints = [
            models.CheckConstraint(
                name="ck_exec_venue_exchange_only",
                condition=(
                    models.Q(venue_type=ExecutionVenueType.EXCHANGE, exchange__isnull=False, platform__isnull=True, counterparty__isnull=True)
                    |
                    ~models.Q(venue_type=ExecutionVenueType.EXCHANGE)
                ),
            ),
            models.CheckConstraint(
                name="ck_exec_venue_platform_only",
                condition=(
                    models.Q(venue_type=ExecutionVenueType.PLATFORM, exchange__isnull=True, platform__isnull=False, counterparty__isnull=True)
                    |
                    ~models.Q(venue_type=ExecutionVenueType.PLATFORM)
                ),
            ),
            models.CheckConstraint(
                name="ck_exec_venue_counterparty_only",
                condition=(
                    models.Q(venue_type=ExecutionVenueType.COUNTERPARTY, exchange__isnull=True, platform__isnull=True, counterparty__isnull=False)
                    |
                    ~models.Q(venue_type=ExecutionVenueType.COUNTERPARTY)
                ),
            ),
            models.CheckConstraint(
                name="ck_exec_venue_otc_internal_empty_refs",
                condition=(
                    models.Q(venue_type__in=[ExecutionVenueType.OTC, ExecutionVenueType.INTERNAL], exchange__isnull=True, platform__isnull=True, counterparty__isnull=True)
                    |
                    ~models.Q(venue_type__in=[ExecutionVenueType.OTC, ExecutionVenueType.INTERNAL])
                ),
            ),
        ]

    def clean(self):
        if self.venue_type == ExecutionVenueType.EXCHANGE:
            if not self.exchange_id:
                raise ValidationError({"exchange": "Exchange is required for exchange venue type."})
            if self.platform_id:
                raise ValidationError({"platform": "Platform must be empty for exchange venue type."})
            if self.counterparty_id:
                raise ValidationError({"counterparty": "Counterparty must be empty for exchange venue type."})

        elif self.venue_type == ExecutionVenueType.PLATFORM:
            if not self.platform_id:
                raise ValidationError({"platform": "Platform is required for platform venue type."})
            if self.exchange_id:
                raise ValidationError({"exchange": "Exchange must be empty for platform venue type."})
            if self.counterparty_id:
                raise ValidationError({"counterparty": "Counterparty must be empty for platform venue type."})

        elif self.venue_type == ExecutionVenueType.COUNTERPARTY:
            if not self.counterparty_id:
                raise ValidationError({"counterparty": "Counterparty is required for counterparty venue type."})
            if self.exchange_id:
                raise ValidationError({"exchange": "Exchange must be empty for counterparty venue type."})
            if self.platform_id:
                raise ValidationError({"platform": "Platform must be empty for counterparty venue type."})

        elif self.venue_type in [ExecutionVenueType.OTC, ExecutionVenueType.INTERNAL]:
            if self.exchange_id or self.platform_id or self.counterparty_id:
                raise ValidationError(
                    "OTC/Internal venue types must not reference exchange, platform, or counterparty."
                )

    def __str__(self):
        return f"{self.code} - {self.name}"