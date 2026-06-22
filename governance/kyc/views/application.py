"""
governance/kyc/views/application.py

Start + resumable wizard + submit. Status is never set here — only via
services/workflow.py. The wizard is server-rendered and save-per-step: each step
persists to the DRAFT before advancing, so a closed tab or a validation error
never loses prior steps. The same surface serves the owner client and an RM
(both pass permissions.can_edit on a DRAFT).

The Documents step is special-cased: instead of a generic formset it renders a
live required-document checklist (services/document_slots.py), where each slot's
required-ness is computed from document_rules.required_documents() at render time.
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from governance.kyc import permissions
from governance.kyc.choices import (
    ApplicationStatus,
    DocumentType,
    StatusAction,
    VerificationStatus,
)
from governance.kyc.forms.section_1 import KYCStartForm
from governance.kyc.models import KYCApplication, KYCDocument
from governance.kyc.services import (
    application_number,
    document_slots,
    section_completion,
    workflow,
)
from governance.kyc.services import wizard as wz
from governance.kyc.services.exceptions import KYCServiceError


@login_required
def start_kyc(request):
    """Create a DRAFT application and allocate its number atomically."""
    if request.method == "POST":
        form = KYCStartForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                application = form.save(commit=False)
                application.owner_user = request.user
                application.created_by = request.user
                application.application_number = application_number.allocate(
                    application.onboarding_market.code
                )
                application.save()
                application.status_logs.create(
                    from_status=None,
                    to_status=ApplicationStatus.DRAFT,
                    action=StatusAction.INITIATE,
                    actor=request.user,
                    reason="Application initiated.",
                )
            return redirect("kyc:wizard", application_id=application.pk)
    else:
        form = KYCStartForm()
    return render(request, "kyc/start.html", {"form": form, "active_tab": "kyc"})


@login_required
def wizard(request, application_id):
    """Entry point: jump to the first incomplete step (or the review step)."""
    application = get_object_or_404(KYCApplication, pk=application_id)
    if not permissions.can_view(request.user, application):
        return HttpResponseForbidden("Not authorized to view this application.")
    target = wz.first_incomplete_key(application)
    return redirect("kyc:wizard-step", application_id=application.pk, step=target)


@login_required
def wizard_step(request, application_id, step):
    """
    Render or save one wizard step.

    GET  -> render the step bound to already-saved data (so reopening resumes).
    POST -> validate + save the step's form(s) and formset(s) atomically, then
            advance. On error, re-render with errors; nothing prior is lost.
    """
    application = get_object_or_404(KYCApplication, pk=application_id)
    step_obj = wz.STEP_BY_KEY.get(step)
    if step_obj is None:
        raise Http404("Unknown wizard step.")

    # Review is a read-only summary; submission goes through kyc:submit.
    if step_obj.review:
        if not permissions.can_view(request.user, application):
            return HttpResponseForbidden("Not authorized.")
        submittable, errors = section_completion.is_submittable(application)
        return render(request, "kyc/wizard_review.html", {
            "application": application,
            "step": step_obj,
            "steps_status": wz.steps_with_status(application),
            "section_status": section_completion.section_status(application),
            "submittable": submittable,
            "submit_errors": errors,
            "active_tab": "kyc",
        })

    # Documents is a live required-document checklist, not a generic formset.
    if step_obj.key == "documents":
        return _documents_step(request, application)

    if not permissions.can_edit(request.user, application):
        return HttpResponseForbidden("This application is not editable.")

    market_code = application.onboarding_market.code
    is_post = request.method == "POST"
    data = request.POST if is_post else None
    files = request.FILES if is_post else None

    # Build one-to-one section forms, bound to saved instances.
    single_forms = []
    for related_name, form_class, needs_market in step_obj.forms:
        try:
            instance = getattr(application, related_name)
        except ObjectDoesNotExist:
            instance = None
        kwargs = {"instance": instance}
        if needs_market:
            kwargs["market"] = market_code
        form = form_class(data, **kwargs) if is_post else form_class(**kwargs)
        single_forms.append((related_name, form))

    # Build the step's repeating-group formsets.
    formsets = []
    for group in wz.groups_for(application, step_obj):
        formset_cls = wz.GROUP_FORMSETS[group]
        formset = (
            formset_cls(data, files, instance=application, prefix=group)
            if is_post
            else formset_cls(instance=application, prefix=group)
        )
        formsets.append((group, formset))

    if is_post:
        forms_ok = all(f.is_valid() for _, f in single_forms)
        sets_ok = all(fs.is_valid() for _, fs in formsets)
        if forms_ok and sets_ok:
            with transaction.atomic():
                for _related, form in single_forms:
                    obj = form.save(commit=False)
                    obj.application = application
                    if obj.pk is None:
                        obj.created_by = request.user
                    else:
                        obj.updated_by = request.user
                    obj.save()
                for _group, formset in formsets:
                    for obj in formset.save(commit=False):
                        if obj.pk is None:
                            obj.created_by = request.user
                        else:
                            obj.updated_by = request.user
                        obj.save()
                    for gone in formset.deleted_objects:
                        gone.delete()
            nxt = wz.next_key(step) or "review"
            return redirect("kyc:wizard-step", application_id=application.pk, step=nxt)
        # invalid -> fall through and re-render with bound forms (data preserved)

    context = {
        "application": application,
        "step": step_obj,
        "steps_status": wz.steps_with_status(application),
        "single_forms": [(wz.FORM_LABELS.get(rn, rn), f) for rn, f in single_forms],
        "formsets": [
            (
                group,
                wz.GROUP_LABELS[group],
                formset,
                reverse("kyc:ajax-add-row", args=[application.pk, group]),
                wz.GROUP_TEMPLATES[group],
            )
            for group, formset in formsets
        ],
        "prev_step": wz.prev_key(step),
        "active_tab": "kyc",
    }
    return render(request, "kyc/wizard_step.html", context)


def _documents_step(request, application):
    """Required-document checklist step: starred slots computed live, plus extras."""
    if not permissions.can_edit(request.user, application):
        return HttpResponseForbidden("This application is not editable.")

    slot_errors = []

    if request.method == "POST":
        # 1) Per-required-slot uploads (type is implied by the slot).
        for slot in document_slots.required_slots(application):
            uploaded = request.FILES.get(slot.field_name)
            if not uploaded:
                continue
            err = document_slots.validate_upload(uploaded)
            if err:
                slot_errors.append(f"{slot.label}: {err}")
                continue
            KYCDocument.objects.update_or_create(
                application=application,
                document_type=slot.code,
                joint_holder=None,                      # principal documents only
                defaults={
                    "file": uploaded,
                    "original_filename": uploaded.name[:255],
                    "verification_status": VerificationStatus.UNVERIFIED,
                    "updated_by": request.user,
                },
                create_defaults={
                    "file": uploaded,
                    "original_filename": uploaded.name[:255],
                    "verification_status": VerificationStatus.UNVERIFIED,
                    "created_by": request.user,
                    "updated_by": request.user,
                },
            )

        # 2) Optional extra document (free type + file).
        extra_type = request.POST.get("extra-document_type") or ""
        extra_file = request.FILES.get("extra-file")
        if extra_file and extra_type:
            err = document_slots.validate_upload(extra_file)
            if err:
                slot_errors.append(f"Additional document: {err}")
            else:
                KYCDocument.objects.update_or_create(
                    application=application,
                    document_type=extra_type,
                    joint_holder=None,
                    defaults={
                        "file": extra_file,
                        "original_filename": extra_file.name[:255],
                        "verification_status": VerificationStatus.UNVERIFIED,
                        "updated_by": request.user,
                    },
                    create_defaults={
                        "file": extra_file,
                        "original_filename": extra_file.name[:255],
                        "verification_status": VerificationStatus.UNVERIFIED,
                        "created_by": request.user,
                        "updated_by": request.user,
                    },
                )
        elif extra_file and not extra_type:
            slot_errors.append("Choose a document type for the additional file.")

        if not slot_errors:
            nxt = wz.next_key("documents") or "review"
            return redirect("kyc:wizard-step", application_id=application.pk, step=nxt)
        # else fall through and re-render with errors (saved uploads persist)

    context = {
        "application": application,
        "step": wz.STEP_BY_KEY["documents"],
        "steps_status": wz.steps_with_status(application),
        "slots": document_slots.required_slots(application),
        "extras": document_slots.extra_documents(application),
        "document_type_choices": DocumentType.choices,
        "accept_attr": document_slots.ACCEPT_ATTR,
        "slot_errors": slot_errors,
        "prev_step": wz.prev_key("documents"),
        "active_tab": "kyc",
    }
    return render(request, "kyc/wizard_documents.html", context)


@login_required
@require_POST
def submit_application(request, application_id):
    """Move DRAFT/ADDL_INFO -> SUBMITTED via the workflow service."""
    application = get_object_or_404(KYCApplication, pk=application_id)

    # Server-side gate: never trust the client-disabled button alone.
    submittable, completion_errors = section_completion.is_submittable(application)
    if not submittable:
        return render(
            request,
            "kyc/wizard_review.html",
            {
                "application": application,
                "step": wz.STEP_BY_KEY["review"],
                "steps_status": wz.steps_with_status(application),
                "section_status": section_completion.section_status(application),
                "submittable": False,
                "submit_errors": completion_errors,
                "active_tab": "kyc",
            },
            status=400,
        )

    action = (
        StatusAction.RESUBMIT
        if application.application_status == ApplicationStatus.ADDL_INFO
        else StatusAction.SUBMIT
    )
    try:
        workflow.transition(application, action, request.user, reason=request.POST.get("reason"))
    except KYCServiceError as exc:
        return render(
            request,
            "kyc/wizard_review.html",
            {
                "application": application,
                "step": wz.STEP_BY_KEY["review"],
                "steps_status": wz.steps_with_status(application),
                "submit_errors": [str(exc)],
                "submittable": False,
                "active_tab": "kyc",
            },
            status=400,
        )
    return redirect("kyc:dashboard")