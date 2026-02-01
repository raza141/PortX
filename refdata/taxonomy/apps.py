from django.apps import AppConfig


# class TaxonomyConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'taxonomy'


class TaxonomyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "refdata.taxonomy"
    label = "taxonomy"
