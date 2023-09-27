from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum as DbEnum
from sqlalchemy.orm import declarative_base
from enum import Enum as PyEnum


class _TagStatus(PyEnum):
    green = 0
    yellow = 1
    red = 2


class Trailer(declarative_base()):
    __tablename__ = 'trailers'
    # --- #
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String, unique=True)
    vin = Column(String, unique=True)
    license = Column(String, unique=True)
    owner = Column(String)
    year = Column(Integer)
    ai_ends = Column(DateTime)
    is_gps_working = Column(Boolean)
    tag_status = Column(DbEnum(_TagStatus))