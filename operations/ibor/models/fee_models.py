"""
Fee Schedule Models for IBOR Module

Defines fee schedules and rules for broker commissions, taxes, and other trading charges.
Supports tiered pricing and cumulative charge calculations (e.g., SST based on Commission+CDC).
"""

from django.db import models
from decimal import Decimal


class IborFeeSchedule(models.Model):
    """
    Master fee schedule per broker/exchange/asset/currency combination.
    
    Each broker can have multiple schedules for different asset classes and exchanges.
    Schedules are date-effective and can be versioned over time.
    """
    
    schedule_name = models.CharField(
        max_length=200,
        help_text="Descriptive name, e.g., 'SHNI PSX Equity Standard'"
    )
    broker = models.ForeignKey(
        'IborBroker',
        on_delete=models.CASCADE,
        related_name='fee_schedules',
        help_text="Broker to which this schedule applies"
    )
    asset_class = models.CharField(
        max_length=50,
        help_text="EQUITY, DEBT, DERIVATIVE, etc."
    )
    exchange = models.CharField(
        max_length=50,
        blank=True,
        help_text="Specific exchange (PSX, KSE, etc.) or blank for all"
    )
    currency = models.CharField(
        max_length=3,
        default='PKR',
        help_text="Trading currency"
    )
    effective_date = models.DateField(
        help_text="Date from which this schedule is valid"
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when schedule expires (null = no expiry)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Active status"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ibor_fee_schedule'
        ordering = ['-effective_date']
        verbose_name = 'IBOR Fee Schedule'
        verbose_name_plural = 'IBOR Fee Schedules'
    
    def __str__(self):
        return f"{self.schedule_name} ({self.broker.broker_code})"


class IborFeeRule(models.Model):
    """
    Individual fee rule within a schedule.
    
    Each rule represents a specific charge (commission, CDC, SST, etc.) with:
    - Calculation method (percentage of gross, flat amount, cumulative, etc.)
    - Rate/amount
    - Sequence for ordered calculation
    - Optional price tiering
    """
    
    CALCULATION_METHODS = [
        ('PCT_GROSS', 'Percentage of Gross Amount'),
        ('PCT_NET', 'Percentage of Net Amount'),
        ('FLAT', 'Flat Amount'),
        ('PCT_CUMULATIVE', 'Percentage of Cumulative Preceding Charges'),  # NEW for SST
    ]
    
    fee_schedule = models.ForeignKey(
        IborFeeSchedule,
        on_delete=models.CASCADE,
        related_name='rules',
        help_text="Parent fee schedule"
    )
    charge_type = models.ForeignKey(
        'IborChargeType',
        on_delete=models.PROTECT,
        help_text="Type of charge (Commission, CDC, SST, etc.)"
    )
    sequence = models.IntegerField(
        help_text="Order of calculation: 10, 20, 30... (allows future insertions)"
    )
    calculation_method = models.CharField(
        max_length=20,
        choices=CALCULATION_METHODS,
        help_text="How to calculate this charge"
    )
    rate_value = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        help_text="Rate (for percentage) or amount (for flat)"
    )
    
    # Tiered pricing (PSX example: different rates for shares < 10 PKR vs >= 10 PKR)
    min_price = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Minimum share price for this rule to apply"
    )
    max_price = models.DecimalField(
        max_digits=19,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Maximum share price for this rule to apply"
    )
    
    # For cumulative calculations (e.g., SST based on Commission+CDC)
    reference_charge_type_cd = models.CharField(
        max_length=200,
        blank=True,
        help_text="Comma-separated charge codes for cumulative calc: COMM,CDC"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ibor_fee_rule'
        ordering = ['fee_schedule', 'sequence']
        verbose_name = 'IBOR Fee Rule'
        verbose_name_plural = 'IBOR Fee Rules'
        unique_together = [['fee_schedule', 'sequence']]
    
    def __str__(self):
        return f"{self.charge_type.charge_code} (Seq {self.sequence}) - {self.fee_schedule.schedule_name}"
    
    def applies_to_price(self, share_price):
        """
        Check if this rule applies to given share price (tiered pricing logic).
        
        Args:
            share_price: Decimal
            
        Returns:
            bool: True if rule applies
        """
        if self.min_price is not None and share_price < self.min_price:
            return False
        if self.max_price is not None and share_price > self.max_price:
            return False
        return True
