from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TimestampMixin:
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
