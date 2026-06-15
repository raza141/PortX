# operations/ibor/models/fee
# This file consist of two model [IborFeeSchedule, IborFeeRule]



from __future__ import annotations

from django.db import models

from .common import IborTimeStampedModel
from .trade import IborChargeType, IborSide


class IborFeeCalcMethod(models.TextChoices):
    PCT_GROSS = "PCT_GROSS", "Percent of gross"
    FLAT = "FLAT", "Flat amount"
    PER_UNIT = "PER_UNIT", "Per unit"
    PCT_OF_CHARGE = "PCT_OF_CHARGE", "Percent of another charge"
    PCT_CUMULATIVE = "PCT_CUMULATIVE", "Percent of cumulative charges"
    MIN_OF_PCT_OR_ALT = "MIN_OF_PCT_OR_ALT", "Lesser of percent or alternate amount"
    MAX_OF_PCT_OR_ALT = "MAX_OF_PCT_OR_ALT", "Greater of percent or alternate amount"


class IborFeeApplyOn(models.TextChoices):
    GROSS = "GROSS", "Gross amount"
    QUANTITY = "QUANTITY", "Quantity"
    COMMISSION = "COMMISSION", "Commission"
    OTHER = "OTHER", "Other"


class IborFeeAltBasis(models.TextChoices):
    FLAT = "FLAT", "Flat amount"
    PER_UNIT = "PER_UNIT", "Per unit amount"


class IborFeeSchedule(IborTimeStampedModel):
    schedule_name = models.CharField(max_length=120, help_text="Human-friendly fee schedule name.")
    broker = models.ForeignKey(
        "masters.Broker",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_fee_schedules",
        help_text="Optional broker-specific fee schedule.",
    )
    exec_venue = models.ForeignKey(
        "masters.Exchange",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_fee_schedules",
        help_text="Optional exchange/venue-specific fee schedule.",
    )
    source_system = models.CharField(
        max_length=40,
        blank=True,
        default="",
        help_text="Optional source system identifier.",
    )
    asset_class = models.ForeignKey(
        "instruments.AssetClass",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_fee_schedules",
        help_text="Optional asset class filter.",
    )
    asset_sub_class = models.ForeignKey(
        "instruments.AssetSubClass",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_fee_schedules",
        help_text="Optional asset sub-class filter.",
    )
    trade_ccy = models.ForeignKey(
        "masters.Currency",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_fee_schedules",
        help_text="Optional trade currency filter.",
    )
    side = models.CharField(
        max_length=10,
        choices=IborSide.choices,
        blank=True,
        default="",
        help_text="Optional BUY/SELL filter.",
    )
    effective_from = models.DateField(help_text="Date from which this schedule is active.")
    effective_to = models.DateField(null=True, blank=True, help_text="Optional end date.")
    priority = models.PositiveIntegerField(default=100, help_text="Lower number means higher priority.")
    is_default = models.BooleanField(default=False, help_text="Use as fallback schedule if nothing more specific matches.")
    notes = models.TextField(blank=True, default="", help_text="Optional operations notes.")

    class Meta:
        db_table = "ibor_fee_sch"
        ordering = ["priority", "-effective_from", "id"]
        indexes = [
            models.Index(fields=["broker", "effective_from"]),
            models.Index(fields=["exec_venue", "effective_from"]),
            models.Index(fields=["source_system", "effective_from"]),
            models.Index(fields=["is_default"]),
        ]

    def __str__(self) -> str:
        return self.schedule_name


class IborFeeRule(IborTimeStampedModel):
    schedule = models.ForeignKey(
        IborFeeSchedule,
        on_delete=models.CASCADE,
        related_name="rules",
        help_text="Parent fee schedule.",
    )
    sequence_no = models.PositiveIntegerField(default=10, help_text="Processing order of the rule.")
    charge_type_cd = models.CharField(
        max_length=10,
        choices=IborChargeType.choices,
        default=IborChargeType.OTHER,
        help_text="Normalized charge type.",
    )
    description = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Display label for the fee line.",
    )
    calc_method = models.CharField(
        max_length=30,
        choices=IborFeeCalcMethod.choices,
        help_text="How this fee is calculated.",
    )
    apply_on = models.CharField(
        max_length=20,
        choices=IborFeeApplyOn.choices,
        default=IborFeeApplyOn.GROSS,
        help_text="Base used for the percentage leg of the calculation.",
    )
    rate = models.DecimalField(
        max_digits=18,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Percentage rate where applicable, e.g. 0.0015 for 0.15%.",
    )
    flat_amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Flat amount per order where applicable.",
    )
    per_unit_amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Per-unit/share/contract amount where applicable.",
    )
    alternate_amount_basis = models.CharField(
        max_length=20,
        choices=IborFeeAltBasis.choices,
        blank=True,
        default="",
        help_text="For MIN/MAX comparison methods: whether alternate amount is FLAT or PER_UNIT.",
    )
    minimum_amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Optional minimum fee floor.",
    )
    maximum_amount = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Optional maximum fee cap.",
    )
    min_price = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Minimum share price for this rule to apply.",
    )
    max_price = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Maximum share price for this rule to apply.",
    )
    currency = models.ForeignKey(
        "masters.Currency",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_fee_rules",
        help_text="Currency of calculated charge.",
    )
    reference_charge_type_cd = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Referenced charge code(s), e.g. COMM or COMM,CDC for cumulative tax.",
    )
    rounding_dp = models.PositiveSmallIntegerField(default=4, help_text="Decimal places for rounding.")
    is_mandatory = models.BooleanField(default=True, help_text="Whether this charge normally applies.")

    class Meta:
        db_table = "ibor_fee_rule"
        ordering = ["schedule_id", "sequence_no", "id"]
        indexes = [
            models.Index(fields=["schedule", "sequence_no"]),
            models.Index(fields=["charge_type_cd"]),
        ]

    def __str__(self) -> str:
        return f"{self.schedule_id}:{self.sequence_no}:{self.charge_type_cd}"