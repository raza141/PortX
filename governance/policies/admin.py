from django.contrib import admin

from governance.policies.models.mandate import Mandate
from governance.policies.models.ips import IPS

admin.site.register(Mandate)
admin.site.register(IPS)