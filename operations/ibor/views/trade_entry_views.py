# operations/ibor/views/trade_entry_views.py
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from operations.ibor.models.trade import IborTradeEvent
from operations.ibor.services.trade_booking import TradeBookingService


from refdata.masters.models.exchange import Exchange
import json

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
        
        exchanges = Exchange.objects.all().values('exchange_id', 'settlement_offset')
        exchanges_data = {e['exchange_id']: e['settlement_offset'] for e in exchanges}
        
        return render(request, self.template_name, {
            "form": form,
            "charge_formset": charge_formset,
            "exchanges_data": json.dumps(exchanges_data),
        })

    def post(self, request, *args, **kwargs):
        post_data = request.POST.copy()
        post_data["action"] = request.POST.get("submit_action", "book")

        form, charge_formset = self._get_forms(data=post_data)

        if not form.is_valid() or not charge_formset.is_valid():
            exchanges = Exchange.objects.all().values('exchange_id', 'settlement_offset')
            exchanges_data = {e['exchange_id']: e['settlement_offset'] for e in exchanges}
            return render(request, self.template_name, {
                "form": form,
                "charge_formset": charge_formset,
                "exchanges_data": json.dumps(exchanges_data),
            })

        action = form.cleaned_data.get("action", "book")

        with transaction.atomic():
            trade = form.save()
            charge_formset.instance = trade
            charge_formset.save()

            # ✅ ADD THIS NEW BLOCK HERE - Save auto-calculated charges
            from operations.ibor.models.trade import IborChargeComponent
            auto_count = int(request.POST.get('auto_charges_count', 0))
            for idx in range(auto_count):
                charge_type = request.POST.get(f'auto_charge_{idx}_type')
                description = request.POST.get(f'auto_charge_{idx}_desc', '')
                rate = request.POST.get(f'auto_charge_{idx}_rate') or None
                amount = request.POST.get(f'auto_charge_{idx}_amount')
                ccy_id = request.POST.get(f'auto_charge_{idx}_ccy') or None

                if charge_type and amount:
                    IborChargeComponent.objects.create(
                        trade=trade,
                        charge_type_cd=charge_type,
                        description=description,
                        rate=Decimal(rate) if rate else None,
                        amount=Decimal(amount),
                        cost_ccy_id=int(ccy_id) if ccy_id else None,
                        override_flag=False,  # Auto-generated from fee engine
                        source_reference=f'FEE_ENGINE_{idx}',
                    )

            # Continue with existing trade booking logic
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