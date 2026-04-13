from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.user import  UserLogin, UserRegister
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/register")
def register_user(user: UserRegister, response: Response, db: Session = Depends(get_db)):
    token = AuthService.register_user(db, user)
    
    response.set_cookie(key="access_token", value=token["access_token"], httponly=True)
    response.set_cookie(key="refresh_token", value=token["refresh_token"], httponly=True)
    return {"access_token": token["access_token"], 
            "refresh_token": token["refresh_token"]}


@router.post("/login")
def login_user(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    token = AuthService.login_user(db, user)
    response.set_cookie(key="access_token", value=token["access_token"], httponly=True)
    response.set_cookie(key="refresh_token", value=token["refresh_token"], httponly=True)
    return {"access_token": token["access_token"], 
            "refresh_token": token["refresh_token"]}

@router.post("/refresh")
def refresh(response: Response, db: Session = Depends(get_db), access_token: str = Cookie(None), refresh_token: str = Cookie(None)):
    token = AuthService.refresh(db, access_token, refresh_token)
    
    response.set_cookie(key="access_token", value=token["access_token"], httponly=True)
    response.set_cookie(key="refresh_token", value=token["refresh_token"], httponly=True)
    return {"access_token": token["access_token"], 
            "refresh_token": token["refresh_token"]}

@router.post("/logout")  
def logout(response: Response, db: Session = Depends(get_db), access_token: str = Cookie(None), refresh_token: str = Cookie(None)):
    AuthService.logout(db, access_token, refresh_token)

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

@router.post("/logout-all")
def logout_all(response: Response, db: Session = Depends(get_db), refresh_token: str = Cookie(None)):
    AuthService.logout_all(db, refresh_token)

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")