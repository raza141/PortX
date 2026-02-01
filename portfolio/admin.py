from django.contrib import admin

# Register your models here.

from .models.account import Account
from .models.portfolio import Portfolio


admin.site.register(Account)
admin.site.register(Portfolio)
# admin.site.register(PortfolioAccount)
