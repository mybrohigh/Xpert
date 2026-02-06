"""
Сервис для управления прямыми конфигурациями
Обход белого списка и прямая синхронизация с Marzban
"""

import logging
import json
import os
from typing import List, Optional, Dict
from datetime import datetime

from app.xpert.models import DirectConfig
from app.xpert.checker import checker

logger = logging.getLogger(__name__)


class DirectConfigService:
    """Сервис для управления прямыми конфигурациями"""
    
    def __init__(self):
        self.storage_file = "data/direct_configs.json"
        self.configs: List[DirectConfig] = []
        self.next_id = 1
        self._load_configs()
    
    def _load_configs(self):
        """Загрузка конфигураций из файла"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.configs = [DirectConfig.from_dict(config_data) for config_data in data.get('configs', [])]
                self.next_id = data.get('next_id', 1)
                
                logger.info(f"Loaded {len(self.configs)} direct configs")
            else:
                self.configs = []
                self.next_id = 1
                
        except Exception as e:
            logger.error(f"Failed to load direct configs: {e}")
            self.configs = []
            self.next_id = 1
    
    def _save_configs(self):
        """Сохранение конфигураций в файл"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            
            data = {
                'configs': [config.to_dict() for config in self.configs],
                'next_id': self.next_id
            }
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(self.configs)} direct configs")
            
        except Exception as e:
            logger.error(f"Failed to save direct configs: {e}")
    
    def add_config(self, raw: str, remarks: Optional[str] = None, added_by: str = "admin") -> DirectConfig:
        """Добавление новой прямой конфигурации"""
        try:
            # Парсинг и валидация конфига
            result = checker.process_config(raw)
            
            if not result:
                raise ValueError("Invalid configuration format")
            
            # Создание объекта конфигурации
            config = DirectConfig(
                id=self.next_id,
                raw=raw,
                protocol=result["protocol"],
                server=result["server"],
                port=result["port"],
                remarks=remarks or result["remarks"],
                ping_ms=result["ping_ms"],
                jitter_ms=result["jitter_ms"],
                packet_loss=result["packet_loss"],
                is_active=result["is_active"],
                bypass_whitelist=True,  # Всегда обходить белый список
                auto_sync_to_marzban=True,  # Автоматически синхронизировать
                added_at=datetime.utcnow().isoformat(),
                added_by=added_by
            )
            
            self.configs.append(config)
            self.next_id += 1
            self._save_configs()
            
            logger.info(f"Added direct config: {config.protocol}://{config.server}:{config.port}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to add direct config: {e}")
            raise
    
    def get_all_configs(self) -> List[DirectConfig]:
        """Получение всех прямых конфигураций"""
        return self.configs.copy()
    
    def get_active_configs(self) -> List[DirectConfig]:
        """Получение активных прямых конфигураций"""
        return [config for config in self.configs if config.is_active]
    
    def get_config_by_id(self, config_id: int) -> Optional[DirectConfig]:
        """Получение конфигурации по ID"""
        return next((config for config in self.configs if config.id == config_id), None)
    
    def toggle_config(self, config_id: int) -> Optional[DirectConfig]:
        """Переключение статуса конфигурации"""
        config = self.get_config_by_id(config_id)
        if config:
            config.is_active = not config.is_active
            self._save_configs()
            logger.info(f"Toggled direct config {config_id}: {config.is_active}")
        return config
    
    def delete_config(self, config_id: int) -> bool:
        """Удаление конфигурации"""
        config = self.get_config_by_id(config_id)
        if config:
            self.configs.remove(config)
            self._save_configs()
            logger.info(f"Deleted direct config {config_id}")
            return True
        return False
    
    def update_config_ping(self, config_id: int, ping_ms: float, packet_loss: float = 0.0):
        """Обновление пинга и потерь для конфигурации"""
        config = self.get_config_by_id(config_id)
        if config:
            config.ping_ms = ping_ms
            config.packet_loss = packet_loss
            self._save_configs()
    
    def get_configs_for_subscription(self) -> List[DirectConfig]:
        """Получение конфигураций для подписки (только активные)"""
        return [config for config in self.configs if config.is_active]
    
    def get_stats(self) -> Dict:
        """Получение статистики прямых конфигураций"""
        total = len(self.configs)
        active = len([c for c in self.configs if c.is_active])
        
        # Статистика по протоколам
        protocols = {}
        for config in self.configs:
            protocol = config.protocol.upper()
            protocols[protocol] = protocols.get(protocol, 0) + 1
        
        return {
            "total_configs": total,
            "active_configs": active,
            "inactive_configs": total - active,
            "protocols": protocols,
            "bypass_whitelist_count": len([c for c in self.configs if c.bypass_whitelist]),
            "auto_sync_count": len([c for c in self.configs if c.auto_sync_to_marzban])
        }


# Глобальный экземпляр сервиса
direct_config_service = DirectConfigService()
