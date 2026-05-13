from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_all(db: Session) -> list[User]:
        return db.query(User).all()

    @staticmethod
    def create(db: Session, username: str, hashed_password: str) -> User:
        user = User(username=username, password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_role(db: Session, user: User, role: str) -> User:
        user.role = role
        db.commit()
        db.refresh(user)
        return user