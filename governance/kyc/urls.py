"""governance/kyc/urls.py — KYC routes (app_name='kyc')."""
from django.urls import path

from governance.kyc.views import ajax, application, dashboard, documents, review

app_name = "kyc"

urlpatterns = [
    path("", dashboard.kyc_dashboard, name="dashboard"),
    path("start/", application.start_kyc, name="start"),
    path("<int:application_id>/wizard/", application.wizard, name="wizard"),
    path("<int:application_id>/wizard/<str:step>/", application.wizard_step, name="wizard-step"),
    path("<int:application_id>/submit/", application.submit_application, name="submit"),

    # Review
    path("review/", review.review_queue, name="review-queue"),
    path("escalations/", review.escalations, name="escalations"),
    path("<int:application_id>/decide/", review.decide, name="decide"),

    # Documents
    path("<int:application_id>/documents/upload/", documents.upload_document, name="upload-document"),
    path("documents/<int:document_id>/verify/", documents.verify_document, name="verify-document"),

    # AJAX
    path("<int:application_id>/section/<str:section>/save/", ajax.save_section, name="ajax-save-section"),
    path("<int:application_id>/validate/", ajax.validate_application, name="ajax-validate"),
    path("<int:application_id>/row/<str:group>/add/", ajax.add_row, name="ajax-add-row"),
]