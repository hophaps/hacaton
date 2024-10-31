from sqlalchemy import create_engine, Column, Integer, Boolean, Text, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///users.db"
DATA_NEWS = "sqlite:///news.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True)
    is_authorized = Column(Boolean, default=False)
    name = Column(String(100))
    interests = Column(Text)
    role = Column(String(100))
    tg_id = Column(Integer, unique=True)


def create_user_table():
    Base.metadata.create_all(engine)


def add_tg_id(user_id, tg_id, is_authorized=True):
    with Session() as session:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user is not None:
            # Обновляем tg_id и статус авторизации
            user.tg_id = tg_id
            user.is_authorized = is_authorized
            session.commit()
        else:
            print("Пользователь не найден.")


def get_user_by_id(user_id):
    with Session() as session:
        return session.query(User).filter_by(user_id=user_id).first()


def get_user_by_tg_id(tg_id):
    with Session() as session:
        return session.query(User).filter_by(tg_id=tg_id).first()


def get_role_by_user_id(tg_id):
    with Session() as session:
        user = session.query(User).filter(User.tg_id == tg_id).first()
        return user.role if user else None


def get_interest(tg_id):
    with Session() as session:
        user = session.query(User).filter(User.tg_id == tg_id).first()
        return user.interests if user else None
