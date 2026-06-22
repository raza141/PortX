# governance/kyc/admin/base.py


class KYCAuditAdminMixin:
    """Stamp created_by/updated_by from the request user for KYCAuditBase models."""
    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if hasattr(obj, "created_by_id"):
                if not obj.created_by_id:
                    obj.created_by = request.user
                obj.updated_by = request.user
            obj.save()
        formset.save_m2m()
        for gone in formset.deleted_objects:
            gone.delete()