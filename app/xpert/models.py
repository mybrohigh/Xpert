from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
from app.db.base import Base


class SubscriptionSource(Base):
    __tablename__ = "subscription_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False, unique=True)
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    last_fetched = Column(DateTime, nullable=True)
    config_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AggregatedConfig(Base):
    __tablename__ = "aggregated_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    raw = Column(Text, nullable=False)
    protocol = Column(String(50), nullable=False)
    server = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    remarks = Column(String(255), nullable=True)
    source_id = Column(Integer, nullable=True)
    ping_ms = Column(Float, default=999.0)
    jitter_ms = Column(Float, default=0.0)
    packet_loss = Column(Float, default=0.0)
    is_active = Column(Boolean, default=False)
    last_check = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
