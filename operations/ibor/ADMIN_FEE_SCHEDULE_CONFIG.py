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
    fields = [
        'charge_type',
        'sequence',
        'calculation_method',
        'rate_value',
        'min_price',
        'max_price',
        'reference_charge_type_cd',
    ]
    ordering = ['sequence']
    
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
        'exchange',
        'currency',
        'effective_date',
        'expiry_date',
        'is_active',
    ]
    list_filter = [
        'broker',
        'asset_class',
        'exchange',
        'currency',
        'is_active',
    ]
    search_fields = ['schedule_name', 'broker__broker_name']
    
    inlines = [IborFeeRuleInline]
    
    fieldsets = (
        ('Schedule Details', {
            'fields': ('schedule_name', 'broker', 'asset_class', 'exchange', 'currency')
        }),
        ('Effective Dates', {
            'fields': ('effective_date', 'expiry_date', 'is_active')
        }),
    )
    
    date_hierarchy = 'effective_date'


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
        'chargetypecd',
        'description',
        'rate',
        'amount',
        'costccy',
        'iswithholding',
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
        'tradedt',
        'portfolio',
        'instrument',
        'side',
        'quantity',
        'price',
        'tradeccy',
        'statecd',
        'bookstscd',
    ]
    list_filter = [
        'statecd',
        'bookstscd',
        'side',
        'portfolio',
        'broker',
        'tradedt',
    ]
    search_fields = [
        'externalref',
        'instrument__symbol',
        'portfolio__portfolio_code',
    ]
    
    inlines = [IborChargeComponentInline]
    
    fieldsets = (
        ('Source & Reference', {
            'fields': ('sourcesystem', 'externalref', 'versionno', 'replacestrade')
        }),
        ('Portfolio & Account', {
            'fields': ('portfolio', 'account', 'broker', 'execvenue')
        }),
        ('Instrument', {
            'fields': ('instrument', 'assetclass', 'assetsubclass')
        }),
        ('Trade Details', {
            'fields': ('side', 'quantity', 'price', 'tradeccy', 'settleccy')
        }),
        ('Dates', {
            'fields': ('tradedt', 'settledt')
        }),
        ('Economics', {
            'fields': ('grossamount', 'netamount'),
            'description': 'Charges will be added below in the Charges section'
        }),
        ('Lifecycle', {
            'fields': ('statecd', 'statets', 'bookstscd', 'bookts', 'bookerrtxt'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('memo',),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'tradedt'
    
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
