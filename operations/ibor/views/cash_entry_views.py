# operations/ibor/views/cash_entry_views.py
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from operations.ibor.models.cash_ledger import IborCashEvent
from operations.ibor.forms.cash_forms import IborCashEntryForm

class IborCashCreateView(CreateView):
    model = IborCashEvent
    form_class = IborCashEntryForm
    template_name = 'ibor/trade/cash_form.html'
    success_url = reverse_lazy('ibor:cash-create')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'cash'
        return context

    def form_valid(self, form):
        """
        Interceptor to ensure ledger consistency.
        If an FX rate is used, the 'amount' represents the value in the 
        account's functional currency (e.g., PKR).
        """
        instance = form.save(commit=False)

        # Logic: If FX rate is present, the entry belongs in the Account's currency
        if instance.fx_rate and instance.account:
            instance.currency = instance.account.currency

        instance.save()
        messages.success(self.request, "Cash event saved successfully.")
        return super().form_valid(form)
