from django.contrib import admin

# Register your models here.

from operations.ibor.models.trade import IborTradeEvent
from operations.ibor.models.cash_ledger import IborCashEvent
from operations.ibor.models.position_lot import PositionLot
from operations.ibor.models.market import IborPriceSnapshot, IborFxOverride
from operations.ibor.models.lot import IborTaxLot, IborLotConsumption



admin.site.register(IborCashEvent)
admin.site.register(PositionLot)
admin.site.register(IborTradeEvent)
admin.site.register(IborFxOverride)
admin.site.register(IborPriceSnapshot)
admin.site.register(IborTaxLot)
admin.site.register(IborLotConsumption)