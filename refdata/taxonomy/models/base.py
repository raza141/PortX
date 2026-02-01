from django.conf import settings
from django.db import models


class AuditModel(models.Model):
    """
    Standard audit fields (institution-style).
    Use created_by as FK if you want linkage to Django users.
    """
    created_by = models.IntegerField(default=101)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
