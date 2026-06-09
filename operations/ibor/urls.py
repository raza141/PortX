from django.urls import path

from operations.ibor.views import IborTradeCreateView

app_name = "ibor"

urlpatterns = [
    path("trades/new/", IborTradeCreateView.as_view(), name="ibor-trade-create"),
]