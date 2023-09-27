from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.orm import declarative_base

class Truck(declarative_base()):
    __tablename__ = 'trucks'
    # --- #
    id = Column(Integer, primary_key=True, autoincrement=True)
    number = Column(String, unique=True)
    vin = Column(String, unique=True)
    license = Column(String, unique=True)
    owner = Column(String)
    year = Column(Integer)
    ai_ends = Column(DateTime)
    is_rental = Column(Boolean)