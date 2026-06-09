from decimal import Decimal

from django import forms

from operations.ibor.models.trade import IborTradeEvent, IborSide


class IborTradeForm(forms.ModelForm):
    side = forms.ChoiceField(
        choices=IborSide.choices,
        widget=forms.Select(attrs={"class": "form-input"}),
        required=True,
        label="Action",
    )

    action = forms.ChoiceField(
        choices=[
            ("save", "Save only"),
            ("book", "Save & Book"),
        ],
        initial="book",
        widget=forms.HiddenInput(),
        required=False,
    )

    fx_rate = forms.DecimalField(
        required=False,
        decimal_places=8,
        max_digits=20,
        initial=Decimal("1"),
        label="FX rate",
        help_text="Optional manual FX rate for reference.",
    )

    class Meta:
        model = IborTradeEvent
        fields = [
            "source_system",
            "external_ref",
            "portfolio",
            "account",
            "broker",
            "exec_venue",
            "instrument",
            "side",
            "quantity",
            "price",
            "trade_ccy",
            "settle_ccy",
            "trade_dt",
            "settle_dt",
            "gross_amount",
            "net_amount",
            "memo",
        ]
        widgets = {
            "source_system": forms.TextInput(attrs={"class": "form-input"}),
            "external_ref": forms.TextInput(attrs={"class": "form-input"}),
            "portfolio": forms.Select(attrs={"class": "form-input"}),
            "account": forms.Select(attrs={"class": "form-input"}),
            "broker": forms.Select(attrs={"class": "form-input"}),
            "exec_venue": forms.Select(attrs={"class": "form-input"}),
            "instrument": forms.Select(attrs={"class": "form-input"}),
            "quantity": forms.NumberInput(attrs={"class": "form-input", "step": "0.0001"}),
            "price": forms.NumberInput(attrs={"class": "form-input", "step": "0.0001"}),
            "trade_ccy": forms.Select(attrs={"class": "form-input"}),
            "settle_ccy": forms.Select(attrs={"class": "form-input"}),
            "trade_dt": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "settle_dt": forms.DateInput(attrs={"type": "date", "class": "form-input"}),
            "gross_amount": forms.NumberInput(attrs={"class": "form-input", "readonly": "readonly"}),
            "net_amount": forms.NumberInput(attrs={"class": "form-input", "readonly": "readonly"}),
            "memo": forms.Textarea(attrs={"rows": 3, "class": "form-input", "placeholder": "Optional notes / thesis..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["source_system"].initial = "manual"
        self.fields["external_ref"].required = False
        self.fields["broker"].required = False
        self.fields["exec_venue"].required = False
        self.fields["settle_ccy"].required = False
        self.fields["gross_amount"].required = False
        self.fields["net_amount"].required = False
        self.fields["memo"].required = False

    def clean(self):
        cleaned_data = super().clean()

        side = cleaned_data.get("side")
        quantity = cleaned_data.get("quantity")
        price = cleaned_data.get("price")
        trade_ccy = cleaned_data.get("trade_ccy")
        settle_ccy = cleaned_data.get("settle_ccy")
        trade_dt = cleaned_data.get("trade_dt")
        settle_dt = cleaned_data.get("settle_dt")

        if side not in {IborSide.BUY, IborSide.SELL}:
            self.add_error("side", "Side must be BUY or SELL.")

        if quantity is not None and quantity <= Decimal("0"):
            self.add_error("quantity", "Quantity must be greater than 0.")

        if price is not None and price <= Decimal("0"):
            self.add_error("price", "Price must be greater than 0.")

        if trade_dt and settle_dt and settle_dt < trade_dt:
            self.add_error("settle_dt", "Settlement date cannot be earlier than trade date.")

        if quantity and price:
            cleaned_data["gross_amount"] = quantity * price

        if trade_ccy and not settle_ccy:
            cleaned_data["settle_ccy"] = trade_ccy

        return cleaned_data