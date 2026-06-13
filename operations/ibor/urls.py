from django.urls import path

from operations.ibor.views import IborTradeCreateView, IborHomeView
from operations.ibor.views.ajax_views import GetFxRateView, GetAccountCurrencyView, GetCurrencyPairView
from operations.ibor.views.cash_entry_views import IborCashCreateView
from operations.ibor.views.cash_api_views import get_cash_balance_api, get_fx_rate_api
from operations.ibor.views.fee_api_views import (
    ibor_fee_quote_api,
    get_fee_schedule_rules_api
)
from operations.ibor.views.position_holding_views import PositionHoldingView


app_name = "ibor"

urlpatterns = [
    path("", IborHomeView.as_view(), name="home"),
    path("trades/", IborTradeCreateView.as_view(), name="trade-create"),
    path("cash/", IborCashCreateView.as_view(), name="cash-create"),
    path("positions/", PositionHoldingView.as_view(), name="positions"),
    path("cash/balance/", get_cash_balance_api, name="cash-balance-api"),
    path("cash/fx-rate/", get_fx_rate_api, name="cash-fx-rate-api"),
    path("cash/get-fx-rate/", GetFxRateView.as_view(), name="get-fx-rate"),
    path("cash/get-account-currency/", GetAccountCurrencyView.as_view(), name="get-account-currency"),
    path("cash/get-currency-pair/", GetCurrencyPairView.as_view(), name="get-currency-pair"),
    path("fees/quote/", ibor_fee_quote_api, name="fee-quote"),
    path("fees/schedule-rules/", get_fee_schedule_rules_api, name="fee-schedule-rules"),
]
