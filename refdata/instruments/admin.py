from django.contrib import admin

# Register your models here.

from .models import  *
from .models.issuer import Issuer
from .models.security_master import SecurityMaster
from .models.security_listing import SecurityListing
from .models.security_identifier import SecurityIdentifier


admin.site.register(AssetClass)
admin.site.register(AssetSubClass)
admin.site.register(Issuer)
admin.site.register(SecurityMaster)
admin.site.register(SecurityListing)
admin.site.register(SecurityIdentifier)

    