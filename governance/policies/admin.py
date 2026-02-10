from django.contrib import admin

from governance.policies.models.mandate import Mandate
from governance.policies.models.ips import IPSVersion

admin.site.register(Mandate)
admin.site.register(IPSVersion)