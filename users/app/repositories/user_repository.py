from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.enums import SystemRole
from app.models.users import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_one(
        self,
        *,
        user_id: UUID | None = None,
        email: str | None = None,
    ):
        stmt = select(User)

        if user_id is not None:
            stmt = stmt.where(User.id == user_id)
        elif email is not None:
            stmt = stmt.where(User.email == email)
        else:
            raise ValueError("No user_id or email")

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
