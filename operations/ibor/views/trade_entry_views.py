from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from operations.ibor.forms import IborTradeForm
from operations.ibor.services.trade_booking import TradeBookingService


class IborTradeCreateView(View):
    template_name = "ibor/trade/trade_form.html"
    success_url = reverse_lazy("ibor-trade-create")

    def get(self, request, *args, **kwargs):
        form = IborTradeForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = IborTradeForm(request.POST)

        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        book_immediately = form.cleaned_data.pop("book_immediately", True)
        trade = form.save()

        if book_immediately:
            result = TradeBookingService.book_trade(trade.id)
            messages.success(
                request,
                f"Trade {result.trade_id} saved and booked. "
                f"Cash events: {result.cash_event_count}, "
                f"Lots: {result.lot_count}, "
                f"Lot consumptions: {result.lot_consumption_count}."
            )
        else:
            messages.success(request, f"Trade {trade.id} saved successfully.")

        return redirect(self.success_url)