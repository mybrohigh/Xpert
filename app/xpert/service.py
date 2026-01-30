import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db import GetDB
from app.xpert.models import SubscriptionSource, AggregatedConfig
from app.xpert.checker import checker

logger = logging.getLogger(__name__)


class XpertService:
    """Сервис агрегации подписок"""
    
    async def add_source(self, db: Session, name: str, url: str, priority: int = 1) -> SubscriptionSource:
        """Добавление источника подписки"""
        source = SubscriptionSource(
            name=name,
            url=url,
            priority=priority,
            enabled=True
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        logger.info(f"Added subscription source: {name}")
        return source
    
    def get_sources(self, db: Session) -> List[SubscriptionSource]:
        """Получение всех источников"""
        return db.query(SubscriptionSource).all()
    
    def get_enabled_sources(self, db: Session) -> List[SubscriptionSource]:
        """Получение активных источников"""
        return db.query(SubscriptionSource).filter(SubscriptionSource.enabled == True).all()
    
    def toggle_source(self, db: Session, source_id: int) -> Optional[SubscriptionSource]:
        """Включение/выключение источника"""
        source = db.query(SubscriptionSource).filter(SubscriptionSource.id == source_id).first()
        if source:
            source.enabled = not source.enabled
            db.commit()
            db.refresh(source)
        return source
    
    def delete_source(self, db: Session, source_id: int) -> bool:
        """Удаление источника"""
        source = db.query(SubscriptionSource).filter(SubscriptionSource.id == source_id).first()
        if source:
            db.delete(source)
            db.commit()
            return True
        return False
    
    def get_active_configs(self, db: Session) -> List[AggregatedConfig]:
        """Получение активных конфигураций"""
        return db.query(AggregatedConfig).filter(AggregatedConfig.is_active == True).order_by(AggregatedConfig.ping_ms).all()
    
    def get_all_configs(self, db: Session) -> List[AggregatedConfig]:
        """Получение всех конфигураций"""
        return db.query(AggregatedConfig).order_by(AggregatedConfig.ping_ms).all()
    
    async def update_subscription(self, db: Session) -> dict:
        """Обновление всех подписок"""
        sources = self.get_enabled_sources(db)
        
        if not sources:
            logger.warning("No enabled sources found")
            return {"active_configs": 0, "total_configs": 0}
        
        # Очищаем старые конфиги
        db.query(AggregatedConfig).delete()
        db.commit()
        
        total_configs = 0
        active_configs = 0
        
        for source in sources:
            try:
                logger.info(f"Fetching configs from: {source.name}")
                configs = await checker.fetch_subscription(source.url)
                
                source.last_fetched = datetime.utcnow()
                source.config_count = len(configs)
                
                source_active = 0
                for raw in configs:
                    result = await checker.process_config(raw)
                    if result:
                        config_obj = AggregatedConfig(
                            raw=result["raw"],
                            protocol=result["protocol"],
                            server=result["server"],
                            port=result["port"],
                            remarks=result["remarks"],
                            source_id=source.id,
                            ping_ms=result["ping_ms"],
                            jitter_ms=result["jitter_ms"],
                            packet_loss=result["packet_loss"],
                            is_active=result["is_active"],
                            last_check=datetime.utcnow()
                        )
                        db.add(config_obj)
                        total_configs += 1
                        if result["is_active"]:
                            active_configs += 1
                            source_active += 1
                
                source.success_rate = (source_active / len(configs) * 100) if configs else 0
                db.commit()
                
                logger.info(f"Source {source.name}: {source_active}/{len(configs)} active configs")
                
            except Exception as e:
                logger.error(f"Failed to process source {source.name}: {e}")
                source.success_rate = 0
                db.commit()
        
        logger.info(f"Subscription update complete: {active_configs}/{total_configs} active configs")
        return {"active_configs": active_configs, "total_configs": total_configs}
    
    def generate_subscription(self, db: Session, format: str = "universal") -> str:
        """Генерация подписки в указанном формате"""
        configs = self.get_active_configs(db)
        
        if format == "base64":
            content = "\n".join([c.raw for c in configs])
            import base64
            return base64.b64encode(content.encode()).decode()
        else:
            return "\n".join([c.raw for c in configs])
    
    def get_stats(self, db: Session) -> dict:
        """Получение статистики"""
        sources = self.get_sources(db)
        configs = self.get_all_configs(db)
        active_configs = [c for c in configs if c.is_active]
        
        return {
            "total_sources": len(sources),
            "enabled_sources": len([s for s in sources if s.enabled]),
            "total_configs": len(configs),
            "active_configs": len(active_configs),
            "avg_ping": sum(c.ping_ms for c in active_configs) / len(active_configs) if active_configs else 0
        }


xpert_service = XpertService()
