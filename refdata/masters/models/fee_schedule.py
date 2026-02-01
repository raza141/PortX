from django.db import models


# Create your models here.
class FeeSchedule(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        EXPIRED = "expired", "Expired"
        DRAFT = "draft", "Draft"

    class BillingFrequency(models.TextChoices):
        DAILY = "daily", "Daily"
        MONTHLY = "monthly", "Monthly"
        QUARTERLY = "quarterly", "Quarterly"
        SEMI_ANNUALLY = "semi_annually", "Semi Annually"
        ANNUALLY = "annually", "Annually"
        ONE_TIME = "one_time", "One Time"

    class BillingTiming(models.TextChoices):
        IN_ADVANCE = "in_advance", "In Advance"
        IN_ARREARS = "in_arrears", "In Arrears"

    class DayCountConvention(models.TextChoices):
        ACTUAL_360 = "actual_360", "Actual/360"
        ACTUAL_365 = "actual_365", "Actual/365"
        THIRTY_360 = "30_360", "30/360"
        THIRTY_365 = "30_365", "30/365"
        ACTUAL_ACTUAL = "actual_actual", "Actual/Actual"

    class AumMeasurement(models.TextChoices):
        END_OF_PERIOD = "end_of_period_AUM", "End of Period AUM"
        AVG_DAILY_AUM = "average_daily_AUM", "Average Daily AUM"
        AVG_MONTHLY_AUM = "average_monthly_AUM", "Average Monthly AUM"
        AVG_QUARTERLY_AUM = "average_quarterly_AUM", "Average Quarterly AUM"

    fee_name = models.CharField(max_length=120, unique=True)
    # Store bps as integer (e.g., 150 = 1.5%)
    mgmt_fee_bps = models.PositiveIntegerField()
    billing_frequency = models.CharField(choices=BillingFrequency.choices, default=BillingFrequency.QUARTERLY, )
    aum_measurement = models.CharField(choices=AumMeasurement.choices, max_length=30,
                                       default=AumMeasurement.AVG_DAILY_AUM, )
    tiering_flag = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE, )
    #
    performance_fee_pct = models.DecimalField(
        max_digits=8, decimal_places=4, null=True, blank=True
    )

    effective_date = models.DateField()

    billing_timing = models.CharField(
        max_length=20,
        choices=BillingTiming.choices,
        default=BillingTiming.IN_ARREARS,
    )
    day_count_convention = models.CharField(
        max_length=15,
        choices=DayCountConvention.choices,
        default=DayCountConvention.ACTUAL_360,
    )
    fee_inclusive_of_tax = models.BooleanField(default=False)
    # Store as a decimal (e.g., 0.0500 = 5%)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=4,
                                   default=0.05)
    # Minimum fee amount charged for the billing period (e.g., AED 50)
    min_fee_amount = models.DecimalField(max_digits=20, decimal_places=2,
                                         default=0.00, null=True, blank=True)
    max_fee_amount = models.DecimalField(max_digits=20, decimal_places=2,
                                         default=0.00, null=True, blank=True)
    # audit fields
    created_by = models.IntegerField(default=101)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'fee_schedule'
        indexes = [
            models.Index(fields=["status", "effective_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.fee_name} ({self.mgmt_fee_bps} bps, {self.billing_frequency})"
