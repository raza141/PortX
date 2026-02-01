from django.db import models


class Country(models.Model):
    country_id = models.IntegerField(primary_key=True)
    country_name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=2)
    currency_code = models.CharField(max_length=3)
    currency_name = models.CharField(max_length=50, null=True, blank=True)
    currency_symbol = models.CharField(max_length=5, null=True, blank=True)
    region = models.CharField(max_length=50, null=True, blank=True)
    investor_friendly = models.BooleanField(default=True)

    #Aduit files
    created_by = models.IntegerField(default=101)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:        # IMPORTANT: Django will NOT try to create/alter this table
        db_table = "country"     # public.country
        managed = True
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.country_name} ({self.country_code})"
