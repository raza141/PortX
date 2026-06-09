from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from operations.ibor.forms import IborChargeFormSet, IborTradeForm
from operations.ibor.models.trade import IborTradeEvent
from operations.ibor.services.trade_booking import TradeBookingService


class IborTradeCreateView(View):
    template_name = "ibor/trade/trade_form.html"
    success_url = reverse_lazy("ibor:trade-create")

    def get(self, request, *args, **kwargs):
        form = IborTradeForm()
        charge_formset = IborChargeFormSet(instance=IborTradeEvent(), prefix="charges")
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "charge_formset": charge_formset,
            },
        )

    def post(self, request, *args, **kwargs):
        post_data = request.POST.copy()
        post_data["action"] = request.POST.get("submit_action", "book")

        form = IborTradeForm(post_data)
        temp_trade = IborTradeEvent()
        charge_formset = IborChargeFormSet(post_data, instance=temp_trade, prefix="charges")

        if not form.is_valid() or not charge_formset.is_valid():
            return render(
                request,
                self.template_name,
                {
                    "form": form,
                    "charge_formset": charge_formset,
                },
            )

        action = form.cleaned_data.get("action", "book")

        with transaction.atomic():
            trade = form.save()

            charge_formset.instance = trade
            charge_formset.save()

            total_charges = sum((charge.amount or Decimal("0")) for charge in trade.charges.all())
            gross = trade.gross_amount or Decimal("0")

            if trade.side == "BUY":
                trade.net_amount = gross + total_charges
            else:
                trade.net_amount = gross - total_charges

            trade.save(update_fields=["net_amount"])

            if action == "book":
                result = TradeBookingService.book_trade(trade.id)
                messages.success(
                    request,
                    f"Trade {result.trade_id} saved and booked. "
                    f"Cash events: {result.cash_event_count}, "
                    f"Lots: {result.lot_count}, "
                    f"Lot consumptions: {result.lot_consumption_count}."
                )
            else:
                messages.success(request, f"Trade {trade.id} saved successfully as unbooked.")

        return redirect(self.success_url)