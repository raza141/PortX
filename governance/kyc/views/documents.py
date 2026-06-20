"""governance/kyc/views/documents.py — attachment upload and verification (thin)."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from governance.kyc import permissions
from governance.kyc.choices import VerificationStatus
from governance.kyc.forms.section_4 import KYCDocumentForm
from governance.kyc.models import KYCApplication, KYCDocument
from governance.kyc.services import document_rules


@login_required
@require_POST
def upload_document(request, application_id):
    application = get_object_or_404(KYCApplication, pk=application_id)
    if not permissions.can_edit(request.user, application):
        return HttpResponseForbidden("Not editable.")
    form = KYCDocumentForm(request.POST, request.FILES, application=application)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)
    document = form.save(commit=False)
    document.application = application
    document.original_filename = getattr(document.file, "name", None)
    document.created_by = request.user
    document.save()
    return JsonResponse(
        {"ok": True, "missing_documents": document_rules.missing_documents(application)}
    )


@login_required
@require_POST
def verify_document(request, document_id):
    document = get_object_or_404(KYCDocument, pk=document_id)
    if not permissions.is_compliance(request.user) and not permissions.is_admin(request.user):
        return HttpResponseForbidden("Only compliance may verify documents.")
    document.verification_status = VerificationStatus.VERIFIED
    document.verified_by = request.user
    document.verified_at = timezone.now()
    document.updated_by = request.user
    document.save(
        update_fields=["verification_status", "verified_by", "verified_at", "updated_by", "updated_at"]
    )
    return JsonResponse({"ok": True})