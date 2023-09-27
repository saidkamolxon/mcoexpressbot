from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, unique=True)
    name = Column(String)
    is_admin = Column(Boolean)
