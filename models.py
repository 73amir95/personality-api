from sqlalchemy import Column, Integer, String, Boolean

from database import Base


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(250), nullable=False, unique=True)
    email = Column(String(250), nullable=False, unique=True)
    first_name = Column(String(250), nullable=False)
    last_name = Column(String(250), nullable=False)
    hashed_password = Column(String(250), nullable=False)
    is_active = Column(Boolean, default=True)