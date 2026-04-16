from fastapi import APIRouter, Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.database import get_db
from app.schemas.team import AddUserToTeam, ChangeUserTeamRole, RoleResponse, TeamCreate, TeamResponse, TeamMembershipResponse, TeamWithRoleResponse
from app.services.team_service import TeamService
from app.services.user_service import UserService
from app.core.permissions import TeamPermission

router = APIRouter()


@router.post("", response_model=TeamResponse)
def create_team(
    team: TeamCreate,
    db: Session = Depends(get_db),
    access_token: str = Cookie(None),
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if UserService.is_user_admin(db, access_token):
        return TeamService.create_team(team, db)
    raise HTTPException(status_code=403, detail="Not permitted")

@router.post("/{team_id}", response_model=TeamMembershipResponse)
def add_user_to_team(
    team_id: UUID,
    user: AddUserToTeam,
    db: Session = Depends(get_db),
    access_token: str = Cookie(None),
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    UserService.is_user_admin(db, access_token)
    return TeamService.add_user_to_team(team_id, user, db)

@router.patch("/{team_id}", response_model=TeamMembershipResponse)
def change_user_team_role(
    team_id: UUID,
    user: ChangeUserTeamRole,
    db: Session = Depends(get_db),
    access_token: str = Cookie(None),
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if TeamService.is_teammember_pm(db, team_id, access_token):
        return TeamService.change_user_team_role(team_id, user, db)
    
    if UserService.is_user_admin(db, access_token):
        return TeamService.change_user_team_role(team_id, user, db)

    raise HTTPException(status_code=403, detail="Not permitted")


@router.delete("/{team_id}/{user_id}")
def remove_user_from_team(
    team_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    access_token: str = Cookie(None),
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if TeamService.is_teammember_pm(db, team_id, access_token):
        return TeamService.remove_user_from_team(team_id, user_id, db)
    
    if UserService.is_user_admin(db, access_token):
        return TeamService.remove_user_from_team(team_id, user_id, db)

    raise HTTPException(status_code=403, detail="Not permitted")

@router.get("/{team_id}/members", response_model=list[TeamMembershipResponse])
def get_teammembers(
    team_id: UUID,
    db: Session = Depends(get_db),
    access_token: str = Cookie(None),
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if TeamService.is_user_in_team(db, team_id, access_token):
        return TeamService.get_members_of_team(db, team_id)

    raise HTTPException(status_code=403, detail="Not permitted")

@router.get("", response_model=list[TeamWithRoleResponse])
def get_teams(
    db: Session = Depends(get_db),
    access_token: str = Cookie(None),
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return TeamService.get_teams_with_user(db, access_token)

@router.get("/all", response_model=list[TeamResponse])
def get_all_teams(
    db: Session = Depends(get_db),
    access_token: str = Cookie(None),
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if UserService.is_user_admin(db, access_token):
        return TeamService.get_all_teams(db)
    raise HTTPException(status_code=403, detail="Not permitted")

@router.get("/{team_id}/getrole/{action}", response_model=RoleResponse)
def get_role_in_team(
    team_id: UUID,
    action: TeamPermission,
    access_token: str = Cookie(None), 
    db: Session = Depends(get_db)
    ):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return TeamService.get_role_in_team(db, access_token, team_id, action)
