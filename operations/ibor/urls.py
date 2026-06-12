from django.urls import path

from operations.ibor.views import IborTradeCreateView
from operations.ibor.views.fee_api_views import ibor_fee_quote_api
from operations.ibor.views.fee_api_views import get_fee_schedule_rules_api

app_name = "ibor"

urlpatterns = [

    path("trades/new/", IborTradeCreateView.as_view(), name="trade-create"),
    path("fees/quote/", ibor_fee_quote_api, name="fee-quote"),
        path("fees/schedule-rules/", get_fee_schedule_rules_api, name="fee-schedule-rules"),

]
