from django.test import TestCase, Client
from django.urls import reverse
from refdata.masters.models.currency import Currency
from refdata.masters.models.currency_pair import CurrencyPair

class GetCurrencyPairViewTest(TestCase):
    def setUp(self):
        self.currency_aed = Currency.objects.create(code='AED')
        self.currency_pkr = Currency.objects.create(code='PKR')
        self.currency_pair = CurrencyPair.objects.create(
            base_currency=self.currency_aed,
            quote_currency=self.currency_pkr,
            code='AED/PKR'
        )
        self.client = Client()

    def test_get_currency_pair(self):
        response = self.client.get(reverse('ibor:get-currency-pair'), {
            'base_currency_id': self.currency_aed.pk,
            'quote_currency_id': self.currency_pkr.pk
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['pair_id'], self.currency_pair.pk)
        self.assertEqual(data['pair_code'], 'AED/PKR')
