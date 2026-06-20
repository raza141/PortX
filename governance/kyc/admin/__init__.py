from django.contrib import admin

# Register your models here.
"""governance/kyc/admin — audit-friendly admin registrations."""
from governance.kyc.admin import application as _application  # noqa: F401
from governance.kyc.admin import documents as _documents  # noqa: F401
from governance.kyc.admin import review as _review  # noqa: F401


