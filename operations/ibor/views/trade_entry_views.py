# operations/ibor/views/trade_entry_views.py
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from operations.ibor.models.trade import IborTradeEvent
from operations.ibor.services.trade_booking import TradeBookingService


class IborTradeCreateView(View):
    template_name = "ibor/trade/trade_form.html"
    success_url = reverse_lazy("ibor:trade-create")

    def _get_forms(self, data=None):
        # Import here — not at module level — avoids app registry timing issue
        from operations.ibor.forms.trade_forms import IborTradeEntryForm
        from operations.ibor.forms.charge_forms import IborChargeFormSet

        if data:
            form = IborTradeEntryForm(data)
            charge_formset = IborChargeFormSet(
                data,
                instance=IborTradeEvent(),
                prefix="charges"
            )
        else:
            form = IborTradeEntryForm()
            charge_formset = IborChargeFormSet(
                instance=IborTradeEvent(),
                prefix="charges"
            )
        return form, charge_formset

    def get(self, request, *args, **kwargs):
        form, charge_formset = self._get_forms()
        return render(request, self.template_name, {
            "form": form,
            "charge_formset": charge_formset,
        })

    def post(self, request, *args, **kwargs):
        post_data = request.POST.copy()
        post_data["action"] = request.POST.get("submit_action", "book")

        form, charge_formset = self._get_forms(data=post_data)

        if not form.is_valid() or not charge_formset.is_valid():
            return render(request, self.template_name, {
                "form": form,
                "charge_formset": charge_formset,
            })

        action = form.cleaned_data.get("action", "book")

        with transaction.atomic():
            trade = form.save()
            charge_formset.instance = trade
            charge_formset.save()

            trade = TradeBookingService.derive_amounts(trade)

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
                messages.success(
                    request,
                    f"Trade {trade.id} saved successfully as unbooked."
                )

        return redirect(self.success_url)