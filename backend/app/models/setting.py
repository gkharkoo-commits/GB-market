from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from backend.app.models.base import Base

class MarketplaceSetting(Base):
    __tablename__ = "marketplace_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
