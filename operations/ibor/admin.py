from django.contrib import admin

# Register your models here.

from operations.ibor.models.trade import IborTradeEvent
from operations.ibor.models.cash_ledger import IborCashEvent
from operations.ibor.models.market import IborPriceSnapshot, IborFxOverride
from operations.ibor.models.lot import IborTaxLot, IborLotConsumption
from operations.ibor.models.fee import IborFeeRule, IborFeeSchedule
from .ADMIN_FEE_SCHEDULE_CONFIG import (
    IborFeeScheduleAdmin,
    IborTradeEventAdmin
)


admin.site.register(IborTaxLot)
admin.site.register(IborLotConsumption)
admin.site.register(IborCashEvent)
admin.site.register(IborPriceSnapshot)
admin.site.register(IborFxOverride)


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
