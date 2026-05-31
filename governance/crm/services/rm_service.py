#core/crm/services/rm_service.py
from __future__ import annotations

from dataclasses import dataclass
from django.db import transaction
from django.core.exceptions import ValidationError

from governance.crm.models import RM


# this class is like a data container
@dataclass(frozen=True)
class CreateRMResult:
    rm: RM


@transaction.atomic
def create_rm(
    *,
    rm_name: str,
    email: str | None = None,
    phone: str | None = None,
    team: str | None = None,
    branch: str | None = None,
    status: str | None = None,
    created_by: int = 101,
) -> CreateRMResult:
    name = (rm_name or "").strip()
    if not name:
        raise ValidationError("rm_name is required.")

    rm = RM.objects.create(
        rm_name=name,
        email=email or None,
        phone=phone or None,
        team=team or None,
        branch=branch or None,
        status=status or RM.Status.ACTIVE,
        created_by=created_by,
    )
    return CreateRMResult(rm=rm)
