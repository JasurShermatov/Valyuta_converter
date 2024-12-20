# utils/database/models.py
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    DateTime,
    Boolean,
)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True)
    username = Column(String(32), nullable=True)
    full_name = Column(String(128), nullable=True)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    last_active_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)

    def __repr__(self):
        return f"User(id={self.id}, user_id={self.user_id}, username={self.username})"

    @property
    def formatted_created_at(self):
        """Yaratilgan vaqtni formatlab qaytaradi"""
        if self.created_at:
            return self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        return None

    @property
    def formatted_last_active(self):
        """Oxirgi faollik vaqtini formatlab qaytaradi"""
        if self.last_active_at:
            return self.last_active_at.strftime("%Y-%m-%d %H:%M:%S")
        return None
