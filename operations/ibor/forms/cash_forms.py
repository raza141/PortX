# operations/ibor/forms/cash_forms.py
from django import forms
from django.forms import DateInput
from operations.ibor.models.cash_ledger import IborCashEvent


class IborCashEntryForm(forms.ModelForm):
    """
    Form for creating and editing IborCashEvent instances.
    """
    fx_rate = forms.DecimalField(
        decimal_places=4,
        max_digits=28,
        required=False,
        widget=forms.NumberInput(attrs={'step': '0.0001'})
    )

    class Meta:
        model = IborCashEvent
        fields = [
            'portfolio',
            'account',
            'currency',
            'amount',
            'effective_dt',
            'cash_event_type',
            'withdrawal_method',
            'fx_rate',
            'currency_pair',
            'trade',
            'description',
            'state_cd',
        ]
        widgets = {
            'effective_dt': DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class'):
                field.widget.attrs['class'] += ' form-input'
            else:
                field.widget.attrs['class'] = 'form-input'

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.fx_rate and instance.amount:
            instance.amount = instance.amount * instance.fx_rate
        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        account = cleaned_data.get('account')
        currency = cleaned_data.get('currency')
        fx_rate = cleaned_data.get('fx_rate')

        if fx_rate:
            return cleaned_data

        if account and currency and account.ccy_id != currency.pk:
            raise forms.ValidationError(
                f"Account {account.acct_cd} currency ({account.ccy.code if account.ccy else 'N/A'}) "
                f"does not match selected event currency ({currency.code})."
            )
        return cleaned_data
