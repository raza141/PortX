# operations/ibor/views/cash_entry_views.py
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views import View
from operations.ibor.forms.cash_forms import IborCashEntryForm

class IborCashCreateView(View):
    template_name = 'ibor/trade/cash_form.html'
    success_url = reverse_lazy('ibor:cash-create')

    def get(self, request, *args, **kwargs):
        form = IborCashEntryForm()
        return render(request, self.template_name, {'form': form, 'active_tab': 'cash'})

    def post(self, request, *args, **kwargs):
        form = IborCashEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cash event saved successfully.")
            return redirect(self.success_url)
        return render(request, self.template_name, {'form': form, 'active_tab': 'cash'})
