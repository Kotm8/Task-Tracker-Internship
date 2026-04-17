from fastapi import HTTPException
from app.schemas.user import UserRegister, UserLogin
from sqlalchemy.orm import Session
from app.models.users import User
from argon2 import PasswordHasher
from app.services.user_service import UserService
from app.services.jwt_service import JWTService
from app.repositories.user_repository import UserRepository

ph = PasswordHasher()


class AuthService:
    
    @staticmethod
    def register_user(db: Session, user: UserRegister):
        db_user = UserService.create_user(db, User(  
            username=user.username,
            email=user.email,
            password=user.password 
        ))
        db_access_token = JWTService.create_access_token(data={"sub": str(db_user.id)})
        JWTService.save_access_token(db, db_user, db_access_token)
        db_refresh_token = JWTService.create_refresh_token(data={"sub": str(db_user.id)})
        JWTService.save_refresh_token(db, db_user, db_refresh_token)

        return {"access_token": db_access_token,
                "refresh_token": db_refresh_token}
    
    @staticmethod
    def login_user(db: Session, user: UserLogin):
        user_repo = UserRepository(db)
        db_user = user_repo.get_one(email=user.email)
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            ph.verify(db_user.password, user.password)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid password")
        db_access_token = JWTService.create_access_token(data={"sub": str(db_user.id)})
        JWTService.save_access_token(db, db_user, db_access_token)
        db_refresh_token = JWTService.create_refresh_token(data={"sub": str(db_user.id)})
        JWTService.save_refresh_token(db, db_user, db_refresh_token)

        return {"access_token": db_access_token,
                "refresh_token": db_refresh_token}
    
    @staticmethod
    def refresh(db: Session, access_token: str, refresh_token: str):
        user_repo = UserRepository(db)
        user_id = JWTService.validate_refresh_token(db, refresh_token)
        
        db_user = user_repo.get_one(user_id=user_id)
        
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if access_token:
            JWTService.revoke_access_token(db, access_token, ignore_expired=True)
        JWTService.revoke_refresh_token(db, refresh_token)

        db_access_token = JWTService.create_access_token(data={"sub": str(db_user.id)})
        JWTService.save_access_token(db, db_user, db_access_token)
        db_refresh_token = JWTService.create_refresh_token(data={"sub": str(db_user.id)})
        JWTService.save_refresh_token(db, db_user, db_refresh_token)
        
        return {"access_token": db_access_token,
                "refresh_token": db_refresh_token}
    
    @staticmethod
    def logout(db: Session, access_token: str, refresh_token: str):
        JWTService.validate_refresh_token(db, refresh_token)
        
        JWTService.revoke_access_token(db, access_token)
        JWTService.revoke_refresh_token(db, refresh_token)

    @staticmethod
    def logout_all(db: Session, refresh_token: str):
        user_repo = UserRepository(db)
        user_id  = JWTService.validate_refresh_token(db, refresh_token)
        
        db_user = user_repo.get_one(user_id=user_id)
        if not db_user:
            return 

        try:
            JWTService.revoke_all_access_tokens(db, db_user.id)
            JWTService.revoke_all_refresh_tokens(db, db_user.id)
            db.commit()
            return 
        except Exception:
            db.rollback()
            raise
