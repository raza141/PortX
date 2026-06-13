from django.views.generic import TemplateView


class PositionHoldingView(TemplateView):
    # This points to the template file you created earlier
    template_name = "ibor/trade/position_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # You will query your Position/Lot models here later and pass them to the context
        return context