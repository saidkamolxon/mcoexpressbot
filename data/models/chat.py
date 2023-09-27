from sqlalchemy import Column, String, Boolean, Integer, DateTime
from sqlalchemy.orm import declarative_base

class Chat(declarative_base()):
    def __init__(self, table_name : str):
        self.__tablename__ = table_name

        