"""
Интеграция Xpert Panel с Marzban
Автоматическое добавление проверенных конфигураций в Marzban
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from app.db.crud import add_host, get_or_create_inbound
from app.db.models import ProxyInbound, ProxyHost
from app.models.proxy import ProxyHost as ProxyHostModify
from app.xpert.models import AggregatedConfig
from app.xpert.storage import storage
from app import db

logger = logging.getLogger(__name__)


class MarzbanIntegration:
    """Сервис интеграции с Marzban"""
    
    def __init__(self):
        self.db_session = db.SessionLocal()
        
    def __del__(self):
        if hasattr(self, 'db_session'):
            self.db_session.close()
    
    def get_inbound_tag_for_config(self, config: AggregatedConfig) -> str:
        """Получение тега inbound для конкретного конфига"""
        protocol = config.protocol.lower()
        port = config.port
        return f"{protocol}-in-{port}"
    
    def config_to_proxy_host(self, config: AggregatedConfig) -> ProxyHostModify:
        """Конвертация конфигурации в ProxyHost для Marzban"""
        return ProxyHostModify(
            remark=f"Xpert-{config.protocol.upper()}-{config.server[:15]}",
            address=config.server,  # Это будет хост для inbound
            port=config.port,  # Используем оригинальный порт из конфига
            path="",  # Путь будет определяться inbound
            sni=config.server,  # SNI = адрес сервера
            host=config.server,  # Host header = адрес сервера
            security="tls",  # Для TLS протоколов
            alpn="h2,http/1.1",
            fingerprint="chrome"
        )
    
    def sync_active_configs_to_marzban(self) -> Dict:
        """Синхронизация активных конфигов с Marzban"""
        try:
            # Получаем активные конфиги
            active_configs = storage.get_active_configs()
            
            if not active_configs:
                logger.info("No active configs to sync")
                return {"status": "no_configs", "count": 0}
            
            # Группируем по протоколам и портам
            configs_by_inbound = {}
            for config in active_configs:
                inbound_tag = self.get_inbound_tag_for_config(config)
                if inbound_tag not in configs_by_inbound:
                    configs_by_inbound[inbound_tag] = []
                configs_by_inbound[inbound_tag].append(config)
            
            synced_count = 0
            errors = []
            
            # Обрабатываем каждый inbound
            for inbound_tag, configs in configs_by_inbound.items():
                try:
                    result = self._sync_inbound_configs(inbound_tag, configs)
                    synced_count += result["synced"]
                    errors.extend(result.get("errors", []))
                except Exception as e:
                    error_msg = f"Failed to sync inbound {inbound_tag}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            logger.info(f"Marzban sync complete: {synced_count} configs synced")
            
            return {
                "status": "success",
                "total_synced": synced_count,
                "total_configs": len(active_configs),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Marzban integration failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _sync_inbound_configs(self, inbound_tag: str, configs: List[AggregatedConfig]) -> Dict:
        """Синхронизация конфигов для конкретного inbound"""
        # Получаем или создаем inbound
        inbound = get_or_create_inbound(self.db_session, inbound_tag)
        
        # Получаем текущие хосты
        current_hosts = inbound.hosts or []
        current_addresses = {host.address for host in current_hosts}
        
        # Определяем какие хосты добавить
        new_addresses = set()
        synced_count = 0
        errors = []
        
        for config in configs:
            if config.server not in current_addresses:
                new_addresses.add(config.server)
        
        # Добавляем новые хосты
        for config in configs:
            if config.server in new_addresses:
                try:
                    proxy_host = self.config_to_proxy_host(config)
                    
                    # Настраиваем параметры для разных протоколов
                    if config.protocol.lower() == "shadowsocks":
                        # Для Shadowsocks не нужен TLS
                        proxy_host.security = "none"
                        proxy_host.sni = ""
                        proxy_host.alpn = ""
                        proxy_host.fingerprint = ""
                    
                    # Добавляем хост
                    add_host(self.db_session, inbound_tag, proxy_host)
                    synced_count += 1
                    logger.info(f"Added {config.protocol} host: {config.server}:{config.port}")
                    
                except Exception as e:
                    error_msg = f"Failed to add host {config.server}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        return {
            "synced": synced_count,
            "errors": errors
        }
    
    def cleanup_inactive_hosts(self, active_configs: List[AggregatedConfig]) -> Dict:
        """Очистка неактивных хостов из Marzban"""
        try:
            active_addresses = {config.server for config in active_configs}
            removed_count = 0
            errors = []
            
            # Получаем все inbound'ы
            inbounds = self.db_session.query(ProxyInbound).all()
            
            for inbound in inbounds:
                if not inbound.hosts:
                    continue
                
                # Удаляем неактивные хосты
                hosts_to_keep = []
                for host in inbound.hosts:
                    if host.address in active_addresses:
                        hosts_to_keep.append(host)
                    else:
                        try:
                            self.db_session.delete(host)
                            removed_count += 1
                            logger.info(f"Removed inactive host: {host.address}")
                        except Exception as e:
                            error_msg = f"Failed to remove host {host.address}: {str(e)}"
                            logger.error(error_msg)
                            errors.append(error_msg)
                
                inbound.hosts = hosts_to_keep
            
            self.db_session.commit()
            
            logger.info(f"Cleanup complete: {removed_count} inactive hosts removed")
            
            return {
                "status": "success",
                "removed_count": removed_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Глобальный экземпляр интеграции
marzban_integration = MarzbanIntegration()
