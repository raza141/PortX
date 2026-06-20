"""
governance/kyc/views/ajax.py

AJAX endpoints for the progressive wizard: save/validate a section, add a blank
repeating row, and persist all repeating groups. Thin — delegate to forms/services.
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from governance.kyc import permissions
from governance.kyc.forms.dynamic_rows import (
    GROUP_FORMSETS,
    GROUP_TEMPLATES,
    build_formsets,
)
from governance.kyc.forms.section_1 import KYCPersonalInfoForm
from governance.kyc.forms.section_2 import KYCResidenceForm
from governance.kyc.forms.section_3 import KYCEmploymentForm, KYCSourceOfWealthForm
from governance.kyc.models import KYCApplication
from governance.kyc.services import section_completion

_SECTION_FORMS = {
    "personal": (KYCPersonalInfoForm, "personal_info"),
    "residence": (KYCResidenceForm, "residence"),
    "source_of_wealth": (KYCSourceOfWealthForm, "source_of_wealth"),
    "employment": (KYCEmploymentForm, "employment"),
}


def _load_application(request, application_id, *, edit=False):
    application = get_object_or_404(KYCApplication, pk=application_id)
    allowed = (
        permissions.can_edit(request.user, application)
        if edit
        else permissions.can_view(request.user, application)
    )
    return application, allowed


@login_required
@require_POST
def save_section(request, application_id, section):
    """Validate and persist one wizard section; return JSON + fresh progress."""
    application, allowed = _load_application(request, application_id, edit=True)
    if not allowed:
        return JsonResponse({"ok": False, "error": "Not editable."}, status=403)
    if section not in _SECTION_FORMS:
        return JsonResponse({"ok": False, "error": "Unknown section."}, status=400)

    form_class, related_name = _SECTION_FORMS[section]
    try:
        instance = getattr(application, related_name)
    except ObjectDoesNotExist:
        instance = None

    kwargs = {"instance": instance}
    if section in ("personal", "residence", "source_of_wealth"):
        kwargs["market"] = application.onboarding_market

    form = form_class(request.POST, **kwargs)
    if not form.is_valid():
        return JsonResponse({"ok": False, "errors": form.errors.get_json_data()}, status=400)

    obj = form.save(commit=False)
    obj.application = application
    if instance is None:
        obj.created_by = request.user
    else:
        obj.updated_by = request.user
    obj.save()

    return JsonResponse(
        {"ok": True, "section_status": section_completion.section_status(application)}
    )


@login_required
@require_GET
def validate_application(request, application_id):
    """Return submit-readiness and per-section completion as JSON."""
    application, allowed = _load_application(request, application_id)
    if not allowed:
        return JsonResponse({"ok": False, "error": "Not authorized."}, status=403)

    submittable, errors = section_completion.is_submittable(application)
    return JsonResponse(
        {
            "ok": True,
            "submittable": submittable,
            "errors": errors,
            "section_status": section_completion.section_status(application),
        }
    )


@login_required
@require_GET
def add_row(request, application_id, group):
    """Return one blank, prefix-bound row for a repeating group."""
    application, allowed = _load_application(request, application_id, edit=True)
    if not allowed:
        return JsonResponse({"ok": False, "error": "Not editable."}, status=403)

    formset_cls = GROUP_FORMSETS.get(group)
    template = GROUP_TEMPLATES.get(group)
    if not formset_cls or not template:
        return JsonResponse({"ok": False, "error": "Unknown group."}, status=400)

    try:
        index = int(request.GET.get("index", 0))
        if index < 0:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "error": "Invalid index."}, status=400)

    formset = formset_cls(instance=application, prefix=group)
    html = render_to_string(
        template, {"form": formset.empty_form, "application": application}, request=request
    )
    # empty_form names use the `__prefix__` placeholder; bind it to the real index.
    html = html.replace("__prefix__", str(index))
    return JsonResponse({"ok": True, "html": html, "group": group})


@login_required
@require_POST
def save_rows(request, application_id):
    """Validate and persist all repeating groups in one transaction."""
    application, allowed = _load_application(request, application_id, edit=True)
    if not allowed:
        return HttpResponseForbidden("Not editable.")

    formsets = build_formsets(application, data=request.POST, files=request.FILES)
    if not all(fs.is_valid() for fs in formsets.values()):
        return JsonResponse(
            {
                "ok": False,
                "errors": {g: fs.errors for g, fs in formsets.items() if not fs.is_valid()},
            },
            status=400,
        )
    for fs in formsets.values():
        for obj in fs.save(commit=False):
            if obj.pk is None:
                obj.created_by = request.user
            else:
                obj.updated_by = request.user
            obj.save()
        for gone in fs.deleted_objects:
            gone.delete()
    return JsonResponse({"ok": True})