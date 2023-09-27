# from sqlalchemy import create_engine, Column, String, Boolean, DateTime
# from sqlalchemy.orm import sessionmaker, declarative_base
#
# from data.models import User
#
# engine = create_engine("sqlite:///data/main.db")
# Session = sessionmaker(bind=engine)
#
# Base = declarative_base()
#
# #region <<--- Creating tables if they are not exist --->>
# #Base.metadata.create_all(engine)
# #endregion
#
# session = Session()
#
# users = session.query(User).all()
#
# for user in users:
#     print(user)
#
# session.commit()





# from enum import Enum
#
#
# class Subject(Enum):
#     Math = 1
#     English = 2
#     Russian = 3


# my_subject = Subject.Math
#
# print(my_subject)

