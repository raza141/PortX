from django.contrib import admin

# Register your models here.

from operations.ibor.models.trade import IborTradeEvent
from operations.ibor.models.cash_ledger import IborCashEvent
from operations.ibor.models.position_lot import PositionLot
from operations.ibor.models.market import IborPriceSnapshot, IborFxOverride
from operations.ibor.models.lot import IborTaxLot, IborLotConsumption
from operations.ibor.models.fee import IborFeeRule, IborFeeSchedule


admin.site.register(IborCashEvent)
admin.site.register(PositionLot)
admin.site.register(IborTradeEvent)
admin.site.register(IborFxOverride)
admin.site.register(IborPriceSnapshot)
admin.site.register(IborTaxLot)
admin.site.register(IborLotConsumption)


class IborFeeRuleInline(admin.TabularInline):
    model = IborFeeRule
    extra = 1
    fields = (
        "sequence_no",
        "charge_type_cd",
        "description",
        "calc_method",
        "apply_on",
        "rate",
        "flat_amount",
        "per_unit_amount",
        "minimum_amount",
        "maximum_amount",
        "currency",
        "reference_charge_type_cd",
        "rounding_dp",
        "is_mandatory",
        "is_active",
    )


@admin.register(IborFeeSchedule)
class IborFeeScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "schedule_name",
        "broker",
        "exec_venue",
        "trade_ccy",
        "side",
        "effective_from",
        "effective_to",
        "priority",
        "is_default",
        "is_active",
    )
    list_filter = (
        "broker",
        "exec_venue",
        "trade_ccy",
        "side",
        "is_default",
        "is_active",
    )
    search_fields = (
        "schedule_name",
        "source_system",
        "broker__broker_nm",
    )
    ordering = ("priority", "-effective_from", "id")
    inlines = [IborFeeRuleInline]


@admin.register(IborFeeRule)
class IborFeeRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "schedule",
        "sequence_no",
        "charge_type_cd",
        "description",
        "calc_method",
        "apply_on",
        "rate",
        "flat_amount",
        "per_unit_amount",
        "is_mandatory",
        "is_active",
    )
    list_filter = (
        "charge_type_cd",
        "calc_method",
        "apply_on",
        "is_mandatory",
        "is_active",
    )
    search_fields = (
        "description",
        "schedule__schedule_name",
    )
    ordering = ("schedule", "sequence_no", "id")