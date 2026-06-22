"""
governance/kyc/services/document_slots.py

Presentation helper for the wizard Documents step. Turns the *dynamic* output of
document_rules.required_documents() into render-ready slots, each paired with its
already-uploaded KYCDocument (or None). Required-ness is computed live, so adding
a DocumentType to required_documents() makes a starred slot appear automatically —
no template or constant changes needed (Rules 1, 4, 5).

Also exposes the accepted file types / size cap (Rule 3), used by both the form
input `accept=` hint and server-side validation.
"""
from __future__ import annotations

from dataclasses import dataclass

from governance.kyc.choices import DocumentType
from governance.kyc.services import document_rules

# Rule 3 — industry-standard KYC upload constraints.
ACCEPTED_EXTENSIONS = (".pdf", ".jpg", ".jpeg", ".png")
ACCEPTED_MIME_TYPES = ("application/pdf", "image/jpeg", "image/png")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ACCEPT_ATTR = ",".join(ACCEPTED_EXTENSIONS)

_LABELS = dict(DocumentType.choices)


@dataclass(frozen=True)
class DocumentSlot:
    code: str            # DocumentType value, e.g. "ADDRESS_PROOF"
    label: str           # human label, e.g. "Address Proof / Utility Bill"
    required: bool        # always True for required slots (kept for template clarity)
    uploaded: object      # the KYCDocument instance, or None
    field_name: str       # POST field name for this slot's file input

    @property
    def is_uploaded(self) -> bool:
        return self.uploaded is not None


def _slot_field_name(code: str) -> str:
    """Stable POST field name for a required slot (type is implied by the slot)."""
    return f"reqdoc-{code}"


def required_slots(application) -> list[DocumentSlot]:
    """Render-ready required-document slots, computed live from the rules engine."""
    required = document_rules.required_documents(application)  # dynamic list of codes
    uploaded_by_type = {
        d.document_type: d
        for d in application.documents.all()
        if d.document_type in required and d.joint_holder_id is None
    }
    slots: list[DocumentSlot] = []
    for code in required:
        slots.append(
            DocumentSlot(
                code=code,
                label=_LABELS.get(code, code),
                required=True,
                uploaded=uploaded_by_type.get(code),
                field_name=_slot_field_name(code),
            )
        )
    return slots


def extra_documents(application):
    """Uploaded documents whose type is NOT in the current required set."""
    required = set(document_rules.required_documents(application))
    return [d for d in application.documents.all() if d.document_type not in required]


def validate_upload(uploaded_file) -> str | None:
    """Return an error string if the file is the wrong type/size, else None."""
    name = (uploaded_file.name or "").lower()
    if not name.endswith(ACCEPTED_EXTENSIONS):
        return f"Unsupported file type. Allowed: {', '.join(ACCEPTED_EXTENSIONS)}."
    if uploaded_file.size and uploaded_file.size > MAX_UPLOAD_BYTES:
        mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        return f"File is too large (max {mb} MB)."
    content_type = getattr(uploaded_file, "content_type", None)
    if content_type and content_type not in ACCEPTED_MIME_TYPES:
        return "File content type not allowed."
    return None