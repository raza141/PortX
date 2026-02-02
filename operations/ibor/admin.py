from django.contrib import admin

# Register your models here.

from operations.ibor.models.cash_ledger import CashLedger
from operations.ibor.models.position_lot import PositionLot
from operations.ibor.models.trade import IborTrade

admin.site.register(CashLedger)
admin.site.register(PositionLot)
admin.site.register(IborTrade)