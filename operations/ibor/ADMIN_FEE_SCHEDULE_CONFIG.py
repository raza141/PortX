"""
Django Admin Configuration for IBOR Fee Schedules and Trade Events

This file provides clean admin interfaces with:
- Fee schedule management with inline rules
- Trade event management with inline charges
- Proper formset handling to fix the "messy charges" UI issue
"""

from django.contrib import admin
from operations.ibor.models.fee import IborFeeSchedule, IborFeeRule
from operations.ibor.models.trade import IborTradeEvent, IborChargeComponent


# ============================================================================
# FEE SCHEDULE ADMIN
from operations.ibor.models.trade import IborTradeEvent, IborChargeComponent
# ============================================================================

class IborFeeRuleInline(admin.TabularInline):
    """
    Inline admin for fee rules within a fee schedule.
    Allows adding multiple rules (Commission, CDC, SST, etc.) in one screen.
    """
    model = IborFeeRule
    extra = 1
    fields = (
        "charge_type_cd",
        "sequence_no",
        "description",
        "calc_method",
        "apply_on",
        "rate",
        "flat_amount",
        "per_unit_amount",
        "alternate_amount_basis",
        "minimum_amount",
        "maximum_amount",
        "min_price",
        "max_price",
        "currency",
        "reference_charge_type_cd",
        "rounding_dp",
        "is_mandatory",
        "is_active",
    )

    ordering = ['sequence_no']
    
    # Make it easier to read
    verbose_name = "Fee Rule"
    verbose_name_plural = "Fee Rules (Commission, CDC, SST, etc.)"


@admin.register(IborFeeSchedule)
class IborFeeScheduleAdmin(admin.ModelAdmin):
    """
    Admin for fee schedules with inline rules.
    """
    list_display = [
        'schedule_name',
        'broker',
        'asset_class',
        'exec_venue',
        'trade_ccy',
        'effective_from',
        'effective_to',
        'is_active',
    ]
    list_filter = [
        'broker',
        'asset_class',
        'exec_venue',
        'trade_ccy',
        'is_active',
    ]
    search_fields = ['schedule_name', 'broker__broker_nm']
    
    inlines = [IborFeeRuleInline]
    
    fieldsets = (
        ('Schedule Details', {
            'fields': ('schedule_name', 'broker', 'asset_class', 'exec_venue', 'trade_ccy')
        }),
        ('Effective Dates', {
            'fields': ('effective_from', 'effective_to', 'is_active')
        }),
    )
    
    date_hierarchy = 'effective_from'


# ============================================================================
# TRADE EVENT ADMIN (with clean charges interface)
# ============================================================================

class IborChargeComponentInline(admin.TabularInline):
    """
    Inline admin for charge components within a trade.
    
    THIS FIXES THE MESSY CHARGES UI ISSUE by properly rendering the formset.
    """
    model = IborChargeComponent
    extra = 1
    fields = [
        'charge_type_cd',
        'description',
        'rate',
        'amount',
        'cost_ccy',
        'is_withholding',
    ]
    
    # Make read-only for auto-populated charges in future
    # readonly_fields = []  # Can add logic later to make auto charges readonly
    
    verbose_name = "Charge / Fee"
    verbose_name_plural = "Charges & Fees (Auto + Manual)"
    
    # Custom CSS to highlight auto vs manual charges
    class Media:
        css = {
            'all': ('admin/css/ibor_charges.css',)  # Create this file later
        }


@admin.register(IborTradeEvent)
class IborTradeEventAdmin(admin.ModelAdmin):
    """
    Admin for trade events with inline charges.
    
    This provides a clean interface where:
    - Charges are properly displayed in a table
    - Add/remove buttons work correctly
    - No messy label text appearing
    """
    list_display = [
        'id',
        'trade_dt',
        'portfolio',
        'instrument',
        'side',
        'quantity',
        'price',
        'trade_ccy',
        'state_cd',
        'book_sts_cd',
    ]
    list_filter = [
        'state_cd',
        'book_sts_cd',
        'side',
        'portfolio',
        'broker',
        'trade_dt',
    ]
    search_fields = [
        'external_ref',
        'instrument__symbol',
        'portfolio__portfolio_code',
    ]
    
    inlines = [IborChargeComponentInline]
    
    fieldsets = (
        ('Source & Reference', {
            'fields': ('source_system', 'external_ref', 'version_no', 'replaces_trade')
        }),
        ('Portfolio & Account', {
            'fields': ('portfolio', 'account', 'broker', 'exec_venue')
        }),
        ('Instrument', {
            'fields': ('instrument', 'asset_class', 'asset_sub_class')
        }),
        ('Trade Details', {
            'fields': ('side', 'quantity', 'price', 'trade_ccy', 'settle_ccy')
        }),
        ('Dates', {
            'fields': ('trade_dt', 'settle_dt')
        }),
        ('Economics', {
            'fields': ('gross_amount', 'net_amount'),
            'description': 'Charges will be added below in the Charges section'
        }),
        ('Lifecycle', {
            'fields': ('state_cd', 'state_ts', 'book_sts_cd', 'book_ts', 'book_err_txt'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('memo',),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'trade_dt'
    
    # Actions
    actions = ['mark_as_booked', 'recalculate_charges']
    
    def mark_as_booked(self, request, queryset):
        queryset.update(bookstscd='BOK')
        self.message_user(request, f"{queryset.count()} trades marked as booked.")
    mark_as_booked.short_description = "Mark selected trades as Booked"
    
    def recalculate_charges(self, request, queryset):
        # Placeholder - implement with fee calculator service later
        self.message_user(request, "Charge recalculation not yet implemented.")
    recalculate_charges.short_description = "Recalculate charges (auto-populate)"


# ============================================================================
# STANDALONE CHARGE TYPE ADMIN (optional)
# ============================================================================

# Uncomment if you want to manage charge types separately
# from operations.ibor.models.trade import IborChargeType
# 
# @admin.register(IborChargeType)
# class IborChargeTypeAdmin(admin.ModelAdmin):
#     list_display = ['charge_code', 'charge_name', 'charge_category']
#     search_fields = ['charge_code', 'charge_name']
