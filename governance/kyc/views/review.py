"""governance/kyc/views/review.py — review queue and decision actions (thin)."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from governance.kyc import permissions
from governance.kyc.choices import StatusAction
from governance.kyc.models import KYCApplication
from governance.kyc.selectors import review_queue as review_selectors
from governance.kyc.services import workflow
from governance.kyc.services.exceptions import KYCServiceError


@login_required
def review_queue(request):
    context = {
        "applications": review_selectors.review_queue(request.user),
        "active_tab": "kyc",
    }
    return render(request, "kyc/review_queue.html", context)


@login_required
def escalations(request):
    """Escalated applications awaiting senior-management decision."""
    context = {
        "applications": review_selectors.escalated_queue(request.user),
        "active_tab": "kyc",
    }
    return render(request, "kyc/escalations.html", context)


@login_required
@require_POST
def decide(request, application_id):
    """Apply a review action (start_review/request_info/escalate/approve/reject)."""
    application = get_object_or_404(KYCApplication, pk=application_id)

    if not permissions.can_view(request.user, application):
        return HttpResponseForbidden("Not authorized.")

    action = request.POST.get("action")
    valid_actions = {
        StatusAction.START_REVIEW,
        StatusAction.REQUEST_INFO,
        StatusAction.ESCALATE,
        StatusAction.APPROVE,
        StatusAction.REJECT,
    }
    if action not in valid_actions:
        return JsonResponse({"ok": False, "error": "Invalid action."}, status=400)

    try:
        workflow.transition(
            application,
            action,
            request.user,
            reason=request.POST.get("reason"),
        )
    except KYCServiceError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    return JsonResponse(
        {
            "ok": True,
            "status": application.application_status,
            "application_id": application.pk,
        }
    )