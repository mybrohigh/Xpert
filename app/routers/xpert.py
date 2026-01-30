from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db import Session as DBSession, get_db
from app.xpert.service import xpert_service
from app.xpert.models import SubscriptionSource
import config

router = APIRouter(prefix="/xpert", tags=["Xpert Panel"])


class SourceCreate(BaseModel):
    name: str
    url: str
    priority: int = 1


class SourceResponse(BaseModel):
    id: int
    name: str
    url: str
    enabled: bool
    priority: int
    config_count: int
    success_rate: float
    
    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    total_sources: int
    enabled_sources: int
    total_configs: int
    active_configs: int
    avg_ping: float
    target_ips: List[str]
    domain: str


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_db)):
    """Получение статистики Xpert Panel"""
    stats = xpert_service.get_stats(db)
    stats["target_ips"] = config.XPERT_TARGET_CHECK_IPS
    stats["domain"] = config.XPERT_DOMAIN
    return stats


@router.get("/sources", response_model=List[SourceResponse])
async def get_sources(db: Session = Depends(get_db)):
    """Получение списка источников подписок"""
    return xpert_service.get_sources(db)


@router.post("/sources", response_model=SourceResponse)
async def add_source(source: SourceCreate, db: Session = Depends(get_db)):
    """Добавление источника подписки"""
    try:
        return await xpert_service.add_source(db, source.name, source.url, source.priority)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int, db: Session = Depends(get_db)):
    """Удаление источника подписки"""
    if xpert_service.delete_source(db, source_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Source not found")


@router.post("/sources/{source_id}/toggle")
async def toggle_source(source_id: int, db: Session = Depends(get_db)):
    """Включение/выключение источника"""
    source = xpert_service.toggle_source(db, source_id)
    if source:
        return {"success": True, "enabled": source.enabled}
    raise HTTPException(status_code=404, detail="Source not found")


@router.post("/update")
async def force_update(db: Session = Depends(get_db)):
    """Принудительное обновление подписок"""
    try:
        result = await xpert_service.update_subscription(db)
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs")
async def get_configs(db: Session = Depends(get_db)):
    """Получение списка конфигураций"""
    configs = xpert_service.get_all_configs(db)
    return [
        {
            "id": c.id,
            "protocol": c.protocol,
            "server": c.server,
            "port": c.port,
            "remarks": c.remarks,
            "ping_ms": c.ping_ms,
            "packet_loss": c.packet_loss,
            "is_active": c.is_active
        }
        for c in configs
    ]


@router.get("/sub")
async def get_subscription(
    format: str = "universal",
    db: Session = Depends(get_db)
):
    """Получение агрегированной подписки"""
    content = xpert_service.generate_subscription(db, format)
    
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Profile-Update-Interval": "1",
        "Subscription-Userinfo": f"upload=0; download=0; total=0; expire=0",
        "Profile-Title": "Xpert Panel"
    }
    
    return PlainTextResponse(content=content, headers=headers)
