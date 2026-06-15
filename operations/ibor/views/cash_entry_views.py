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
        if form.cleaned_data.get('fx_rate') and form.cleaned_data.get('account'):
            form.instance.currency = form.cleaned_data['account'].ccy

        messages.success(self.request, "Cash event saved successfully.")
        return super().form_valid(form)
