from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.enums import SystemRole
from app.models.users import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: UUID):
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)
    
    def get_by_email(self, email: str):
        stmt = select(User).where(User.email == email)
        return self.db.scalar(stmt)
    
    def create(self, username: str, email: str, password: str)-> User:
        user = User(username=username, email=email, password=password)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_role(self, user: User, role: SystemRole) -> User:
        user.system_role = role
        self.db.commit()
        self.db.refresh(user)
        return user
