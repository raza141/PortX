from django.contrib import admin

# Register your models here.

from .models.gics import GicsEdition, GicsSector, GicsIndustryGroup, GicsIndustry, GicsSubIndustry
from .models.local_sector import LocalSector, LocalSectorGicsMap

admin.site.register(GicsEdition)
admin.site.register(GicsSector)
admin.site.register(GicsIndustryGroup)
admin.site.register(GicsIndustry)
admin.site.register(GicsSubIndustry)

admin.site.register(LocalSector)
admin.site.register(LocalSectorGicsMap)

