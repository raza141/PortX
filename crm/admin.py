from django.contrib import admin
from django.conf import settings
from .models import RM, Investor


admin.site.register(RM)
admin.site.register(Investor)

# Register your models here.
