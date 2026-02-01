from django.contrib import admin

from .models.country import Country
from .models.exchange import Exchange
from .models.broker import Broker
from .models.benchmark import Benchmark
from .models.fee_schedule import FeeSchedule
from .models.currency import Currency
from .models.currency_pair import CurrencyPair
from .models.fx import FxRateDaily

# Register your models(Table) here.

admin.site.register(Country)
admin.site.register(Exchange)
admin.site.register(Broker)
admin.site.register(Benchmark)
admin.site.register(FeeSchedule)
admin.site.register(Currency)
admin.site.register(CurrencyPair)
admin.site.register(FxRateDaily)


