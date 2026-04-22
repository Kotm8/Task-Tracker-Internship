from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.dependencies.auth import require_team_permission
from app.services.audit_service import AuditService
from app.core.permissions import TeamPermission
from fastapi.responses import StreamingResponse


router = APIRouter()



@router.get("/{team_id}/audit.csv")
async def export_team_audit(
    team_id: UUID,
    mode: Literal["raw", "aggregated"] = Query("aggregated"),
    db: Session = Depends(get_db),
    current_user=Depends(require_team_permission(TeamPermission.GENERATE_REPORT))
):
    if mode == "raw":
        generator = AuditService.generate_team_audit_csv(db, team_id)
        filename = f'team-{team_id}-audit-raw.csv'
    else:
        generator = AuditService.generate_aggregated_team_audit_csv(db, team_id)
        filename = f'team-{team_id}-audit-aggregated.csv'

    return StreamingResponse(
        generator,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
