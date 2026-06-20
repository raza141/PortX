"""
governance/kyc/views/application.py

Start and wizard views. The application number is allocated by the service, never
in the view. Status is never set here — only via services/workflow.py.
"""
"""
governance/kyc/views/application.py

Start and wizard views. The application number is allocated by the service, never
in the view. Status is never set here — only via services/workflow.py.
"""
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from governance.kyc import permissions
from governance.kyc.choices import ApplicationStatus, StatusAction
from governance.kyc.forms.dynamic_rows import build_formsets
from governance.kyc.forms.section_1 import KYCStartForm
from governance.kyc.models import KYCApplication
from governance.kyc.services import application_number, section_completion, workflow
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
    application = get_object_or_404(KYCApplication, pk=application_id)
    if not permissions.can_view(request.user, application):
        return HttpResponseForbidden("Not authorized to view this application.")

    submittable, errors = section_completion.is_submittable(application)
    context = {
        "application": application,
        "formsets": build_formsets(application),
        "section_status": section_completion.section_status(application),
        "submittable": submittable,
        "submit_errors": errors,
        "allowed_actions": workflow.get_allowed_actions(application, request.user),
        "active_tab": "kyc",
    }
    return render(request, "kyc/wizard.html", context)


@login_required
@require_POST
def submit_application(request, application_id):
    """Move DRAFT/ADDL_INFO -> SUBMITTED/UNDER_REVIEW via the workflow service."""
    application = get_object_or_404(KYCApplication, pk=application_id)

    # Server-side gate: never trust the client-disabled button alone.
    submittable, completion_errors = section_completion.is_submittable(application)
    if not submittable:
        return render(
            request,
            "kyc/wizard.html",
            {"application": application, "submit_errors": completion_errors, "active_tab": "kyc"},
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
            "kyc/wizard.html",
            {"application": application, "submit_errors": [str(exc)], "active_tab": "kyc"},
            status=400,
        )
    return redirect("kyc:wizard", application_id=application.pk)