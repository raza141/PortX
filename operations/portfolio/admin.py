from django.contrib import admin

# Register your models here.

from .models.account import Account
from .models.portfolio import Portfolio
from .models.portfolio_account import PortfolioAccountMap

admin.site.register(Account)
admin.site.register(Portfolio)
admin.site.register(PortfolioAccountMap)
