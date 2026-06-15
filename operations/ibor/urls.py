from django.urls import path

from operations.ibor.views import IborTradeCreateView, IborHomeView
from operations.ibor.views.ajax_views import (
    GetFxRateView,
    GetAccountsByPortfolioView,
    GetBrokerByAccountView,
    GetExchangeByBrokerView,
    GetPortfolioControlsView,
    CalculateSettlementDateView,
    GetBrokerCurrencyView,
)
from operations.ibor.views.cash_entry_views import IborCashCreateView
from operations.ibor.views.cash_api_views import get_account_state_api
from operations.ibor.views.fee_api_views import (
    ibor_fee_quote_api,
    get_fee_schedule_rules_api
)
from operations.ibor.views.position_holding_views import PositionHoldingView
from operations.ibor.views.ajax_views import CalculateSettlementDateView

app_name = "ibor"

urlpatterns = [
# ________________________________________________________________________________________________________________
# ________________________________________________________________________________________________________________

    # UI Views (HTML Pages)
# ________________________________________________________________________________________________________________
# ________________________________________________________________________________________________________________

    path("", IborHomeView.as_view(), name="home"),
    path("trades/", IborTradeCreateView.as_view(), name="trade-create"),
    path("cash/", IborCashCreateView.as_view(), name="cash-create"),
    path("positions/", PositionHoldingView.as_view(), name="positions"),



# ________________________________________________________________________________________________________________
# ________________________________________________________________________________________________________________
    # API Endpoints (JSON Data)
# ________________________________________________________________________________________________________________
# _________________________________________________________________________________________________________________

    # API - Market Data (FX & Rates)
    path("api/market/fx-rate/", GetFxRateView.as_view(), name="get-fx-rate"),

    # API - Cash Management
    # Consolidate balance and currency into one 'Account State' call
    path("api/cash/account-state/", get_account_state_api, name="account-state"),

    # API - Portfolio, Accounts & Brokers
    path("api/portfolio/controls/", GetPortfolioControlsView.as_view(), name="get-portfolio-controls"),
    path("api/accounts/by-portfolio/", GetAccountsByPortfolioView.as_view(), name="get-accounts-by-portfolio"),
    path("api/broker/by-account/", GetBrokerByAccountView.as_view(), name="get-broker-by-account"),
    path("api/broker/currency/", GetBrokerCurrencyView.as_view(), name="get-broker-currency"),
    path("api/exchange/by-broker/", GetExchangeByBrokerView.as_view(), name="get-exchange-by-broker"),

    # API - Trading Reference Data
    path("api/calculate-settlement-date/", CalculateSettlementDateView.as_view(), name="calculate-settlement-date"),

    # API - Fees
    path("api/fees/quote/", ibor_fee_quote_api, name="fee-quote"),
    path("api/fees/schedule-rules/", get_fee_schedule_rules_api, name="fee-schedule-rules"),
]
