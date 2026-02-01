from django.db import models


class TimeStampedModel(models.Model):
    """
    Reusable audit timestamps.
    Institution standard: never lose record history; use timestamps not deletes.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True