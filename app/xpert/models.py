from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class SubscriptionSource:
    id: int = 0
    name: str = ""
    url: str = ""
    enabled: bool = True
    priority: int = 1
    last_fetched: Optional[str] = None
    config_count: int = 0
    success_rate: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


@dataclass
class AggregatedConfig:
    id: int = 0
    raw: str = ""
    protocol: str = ""
    server: str = ""
    port: int = 0
    remarks: str = ""
    source_id: int = 0
    ping_ms: float = 999.0
    jitter_ms: float = 0.0
    packet_loss: float = 0.0
    is_active: bool = False
    last_check: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
