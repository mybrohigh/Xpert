from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional

from app.xpert.service import xpert_service
from app.xpert.marzban_integration import marzban_integration
from app.xpert.ping_stats import ping_stats_service
from app.xpert.direct_config_service import direct_config_service
from app.xpert.checker import checker
from app.models.admin import Admin
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


class PingReport(BaseModel):
    server: str
    port: int
    protocol: str
    ping_ms: float
    success: bool


class StatsResponse(BaseModel):
    total_sources: int
    enabled_sources: int
    total_configs: int
    active_configs: int
    avg_ping: float
    target_ips: List[str]
    domain: str


class DirectConfigCreate(BaseModel):
    raw: str
    remarks: Optional[str] = None
    added_by: Optional[str] = "admin"


class DirectConfigResponse(BaseModel):
    id: int
    raw: str
    protocol: str
    server: str
    port: int
    remarks: str
    ping_ms: float
    jitter_ms: float
    packet_loss: float
    is_active: bool
    bypass_whitelist: bool
    auto_sync_to_marzban: bool
    added_at: str
    added_by: str


@router.get("/whitelists")
async def get_whitelists():
    """Получить все белые списки IP"""
    try:
        from app.xpert.cluster_service import whitelist_service
        whitelists = whitelist_service.get_all_whitelists()
        return {
            "whitelists": [
                {
                    "id": w.id,
                    "name": w.name,
                    "description": w.description,
                    "hosts_count": len(w.allowed_hosts),
                    "active_hosts": sum(1 for host in w.allowed_hosts if host.is_active),
                    "created_at": w.created_at,
                    "updated_at": w.updated_at,
                    "is_active": w.is_active
                }
                for w in whitelists
            ],
            "stats": whitelist_service.get_whitelist_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whitelists")
async def create_whitelist(data: dict):
    """Создать новый белый список IP"""
    try:
        from app.xpert.cluster_service import whitelist_service
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if not name:
            raise HTTPException(status_code=400, detail="Whitelist name is required")
        
        whitelist_id = whitelist_service.create_whitelist(name, description)
        return {"whitelist_id": whitelist_id, "message": "IP whitelist created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whitelists/{whitelist_id}/hosts")
async def add_allowed_host(whitelist_id: str, data: dict):
    """Добавить разрешенный хост (IP или домен) в белый список"""
    try:
        from app.xpert.cluster_service import whitelist_service
        
        host = data.get('host', '').strip()
        description = data.get('description', '').strip()
        country = data.get('country', '').strip()
        
        if not host:
            raise HTTPException(status_code=400, detail="Host (IP or domain) is required")
        
        success = whitelist_service.add_allowed_host(
            whitelist_id, host, description, country
        )
        
        if success:
            return {"message": "Allowed host added successfully"}
        else:
            raise HTTPException(status_code=404, detail="Whitelist not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/whitelists/{whitelist_id}/hosts")
async def get_whitelist_hosts(whitelist_id: str):
    """Получить хосты (IP и домены) белого списка"""
    try:
        from app.xpert.cluster_service import whitelist_service
        
        whitelists = whitelist_service.get_all_whitelists()
        whitelist = next((w for w in whitelists if w.id == whitelist_id), None)
        
        if not whitelist:
            raise HTTPException(status_code=404, detail="Whitelist not found")
        
        return {
            "whitelist_id": whitelist_id,
            "whitelist_name": whitelist.name,
            "hosts": [
                {
                    "host": host.host,
                    "description": host.description,
                    "country": host.country,
                    "is_active": host.is_active,
                    "added_at": host.added_at
                }
                for host in whitelist.allowed_hosts
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/whitelists/{whitelist_id}/hosts/{host}/status")
async def update_host_status(whitelist_id: str, host: str, data: dict):
    """Обновить статус хоста"""
    try:
        from app.xpert.cluster_service import whitelist_service
        
        is_active = data.get('is_active', True)
        
        success = whitelist_service.update_host_status(host, is_active)
        
        if success:
            return {"message": "Host status updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Host not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/whitelists/{whitelist_id}")
async def delete_whitelist(whitelist_id: str):
    """Удалить белый список"""
    try:
        from app.xpert.cluster_service import whitelist_service
        
        success = whitelist_service.delete_whitelist(whitelist_id)
        
        if success:
            return {"message": "Whitelist deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Whitelist not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/whitelists/{whitelist_id}/hosts/{host}")
async def delete_host_from_whitelist(whitelist_id: str, host: str):
    """Удалить хост из белого списка"""
    try:
        from app.xpert.cluster_service import whitelist_service
        
        success = whitelist_service.remove_host_from_whitelist(whitelist_id, host)
        
        if success:
            return {"message": "Host removed successfully"}
        else:
            raise HTTPException(status_code=404, detail="Whitelist or host not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/allowed-hosts")
async def get_allowed_hosts():
    """Получить все разрешенные хосты (IP и домены)"""
    try:
        from app.xpert.cluster_service import whitelist_service
        allowed_hosts = whitelist_service.get_all_allowed_hosts()
        
        return {
            "hosts": list(allowed_hosts),
            "total": len(allowed_hosts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/filter-servers")
async def filter_servers_by_host(data: dict):
    """Отфильтровать сервера по белому списку хостов"""
    try:
        from app.xpert.ip_filter import host_filter
        
        server_configs = data.get('servers', [])
        
        if not server_configs:
            raise HTTPException(status_code=400, detail="No servers provided")
        
        # Фильтрация серверов
        filtered_servers = host_filter.filter_servers(server_configs)
        
        return {
            "total_servers": len(server_configs),
            "allowed_servers": len(filtered_servers),
            "servers": filtered_servers,
            "stats": host_filter.get_filter_stats()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/stats")
async def get_stats():
    """Получение статистики Xpert Panel"""
    return xpert_service.get_stats()


@router.get("/sources")
async def get_sources():
    """Получение списка источников подписок"""
    sources = xpert_service.get_sources()
    return [
        {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "enabled": s.enabled,
            "priority": s.priority,
            "config_count": s.config_count,
            "success_rate": s.success_rate,
            "last_fetched": s.last_fetched
        }
        for s in sources
    ]


@router.post("/sources")
async def add_source(source: SourceCreate):
    """Добавление источника подписки"""
    try:
        s = xpert_service.add_source(source.name, source.url, source.priority)
        return {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "enabled": s.enabled,
            "priority": s.priority,
            "config_count": s.config_count,
            "success_rate": s.success_rate
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sources/{source_id}")
async def delete_source(source_id: int):
    """Удаление источника подписки"""
    if xpert_service.delete_source(source_id):
        return {"success": True}
    raise HTTPException(status_code=404, detail="Source not found")


@router.post("/sources/{source_id}/toggle")
async def toggle_source(source_id: int):
    """Включение/выключение источника"""
    source = xpert_service.toggle_source(source_id)
    if source:
        return {"success": True, "enabled": source.enabled}
    raise HTTPException(status_code=404, detail="Source not found")


@router.post("/update")
async def force_update():
    """Принудительное обновление подписок"""
    try:
        # Увеличиваем таймаут для долгих операций
        import asyncio
        result = await asyncio.wait_for(xpert_service.update_subscription(), timeout=300)  # 5 минут
        return {"success": True, **result}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=408, detail="Update timeout - operation took too long")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configs")
async def get_configs():
    """Получение списка конфигураций"""
    configs = xpert_service.get_all_configs()
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


@router.post("/test-url")
async def test_subscription_url(url_data: dict):
    """Тестирование URL подписки перед добавлением"""
    url = url_data.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        configs = await checker.fetch_subscription(url)
        return {
            "success": True,
            "url": url,
            "config_count": len(configs),
            "sample_configs": configs[:3]  # Показываем первые 3 конфига для примера
        }
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "config_count": 0
        }


@router.post("/sync-marzban")
async def sync_to_marzban():
    """Принудительная синхронизация с Marzban"""
    try:
        result = marzban_integration.sync_active_configs_to_marzban()
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ping-report")
async def report_ping(ping_data: PingReport, user_id: int = 1):
    """Запись результата пинга от пользователя"""
    try:
        ping_stats_service.record_ping(
            server=ping_data.server,
            port=ping_data.port,
            protocol=ping_data.protocol,
            user_id=user_id,
            ping_ms=ping_data.ping_ms,
            success=ping_data.success
        )
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/server-health/{server}/{port}/{protocol}")
async def get_server_health(server: str, port: int, protocol: str):
    """Получение статистики здоровья сервера"""
    try:
        health = ping_stats_service.get_server_health(server, port, protocol)
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ping-stats")
async def get_ping_stats():
    """Получение сводной статистики пингов"""
    try:
        return ping_stats_service.get_stats_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-stats")
async def cleanup_ping_stats(days: int = 7):
    """Очистка старой статистики"""
    try:
        ping_stats_service.cleanup_old_stats(days)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-configs")
async def get_top_configs(limit: int = 10):
    """Получение топ-N конфигов с их score"""
    try:
        configs = xpert_service.get_active_configs()
        
        # Получаем топ конфиги с score
        try:
            from app.xpert.ping_stats import ping_stats_service
            import config as app_config
            
            # Фильтруем здоровые
            healthy_configs = ping_stats_service.get_healthy_configs(configs)
            
            # Получаем топ с score
            top_limit = min(limit, app_config.XPERT_TOP_SERVERS_LIMIT)
            top_configs = ping_stats_service.get_top_configs(healthy_configs, top_limit)
            
            # Добавляем score для отображения
            result = []
            for config in top_configs:
                health = ping_stats_service.get_server_health(config.server, config.port, config.protocol)
                score = 0
                
                if health['healthy'] is None:
                    score = ping_stats_service._calculate_original_score(config)
                elif health['healthy']:
                    score = ping_stats_service._calculate_stats_score(health, config)
                
                result.append({
                    "id": config.id,
                    "protocol": config.protocol,
                    "server": config.server,
                    "port": config.port,
                    "remarks": config.remarks,
                    "ping_ms": config.ping_ms,
                    "packet_loss": config.packet_loss,
                    "is_active": config.is_active,
                    "score": round(score, 2),
                    "health": health
                })
            
            return {"configs": result, "total": len(result)}
            
        except Exception as e:
            # Если статистика недоступна, возвращаем базовые конфиги
            return {"configs": configs[:limit], "total": len(configs[:limit])}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/queue-configs")
async def get_queue_configs():
    """Получение конфигов в очереди (не попавших в топ)"""
    try:
        configs = xpert_service.get_active_configs()
        
        # Получаем топ конфиги
        try:
            from app.xpert.ping_stats import ping_stats_service
            import config as app_config
            
            # Фильтруем здоровые
            healthy_configs = ping_stats_service.get_healthy_configs(configs)
            
            # Получаем топ
            top_limit = app_config.XPERT_TOP_SERVERS_LIMIT
            top_configs = ping_stats_service.get_top_configs(healthy_configs, top_limit)
            
            # Очередь = все здоровые минус топ
            top_servers = {(c.server, c.port, c.protocol) for c in top_configs}
            queue_configs = [
                c for c in healthy_configs 
                if (c.server, c.port, c.protocol) not in top_servers
            ]
            
            return {"configs": queue_configs, "total": len(queue_configs)}
            
        except Exception as e:
            # Если статистика недоступна, возвращаем пустую очередь
            return {"configs": [], "total": 0}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sub")
async def get_subscription(format: str = "universal"):
    """Получение агрегированной подписки"""
    content = xpert_service.generate_subscription(format)
    
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Profile-Update-Interval": "1",
        "Subscription-Userinfo": "upload=0; download=0; total=0; expire=0",
        "Profile-Title": "Xpert Panel"
    }
    
    return PlainTextResponse(content=content, headers=headers)


# Direct Configurations API
@router.get("/direct-configs")
async def get_direct_configs():
    """Получение всех прямых конфигураций"""
    try:
        configs = direct_config_service.get_all_configs()
        return {
            "configs": [
                {
                    "id": c.id,
                    "raw": c.raw,
                    "protocol": c.protocol,
                    "server": c.server,
                    "port": c.port,
                    "remarks": c.remarks,
                    "ping_ms": c.ping_ms,
                    "jitter_ms": c.jitter_ms,
                    "packet_loss": c.packet_loss,
                    "is_active": c.is_active,
                    "bypass_whitelist": c.bypass_whitelist,
                    "auto_sync_to_marzban": c.auto_sync_to_marzban,
                    "added_at": c.added_at,
                    "added_by": c.added_by
                }
                for c in configs
            ],
            "total": len(configs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/direct-configs")
async def add_direct_config(config_data: DirectConfigCreate, admin: Admin = Depends(Admin.get_current)):
    """Добавление одиночной конфигурации в обход белого списка"""
    try:
        config = direct_config_service.add_config(
            raw=config_data.raw,
            remarks=config_data.remarks,
            added_by=config_data.added_by
        )
        
        # Автоматическая синхронизация с Marzban если включена
        if config.auto_sync_to_marzban:
            try:
                marzban_integration.sync_direct_config_to_marzban(config)
            except Exception as e:
                # Не прерываем операцию, но логируем ошибку
                import logging
                logging.warning(f"Failed to sync direct config to Marzban: {e}")
        
        return {
            "id": config.id,
            "message": "Direct config added successfully",
            "config": {
                "id": config.id,
                "protocol": config.protocol,
                "server": config.server,
                "port": config.port,
                "remarks": config.remarks,
                "bypass_whitelist": config.bypass_whitelist,
                "auto_sync_to_marzban": config.auto_sync_to_marzban
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/direct-configs/batch")
async def add_direct_configs_batch(configs_data: dict, admin: Admin = Depends(Admin.get_current)):
    """Массовое добавление конфигураций"""
    try:
        raw_configs = configs_data.get('configs', [])
        added_by = configs_data.get('added_by', 'admin')
        
        if not raw_configs:
            raise HTTPException(status_code=400, detail="No configs provided")
        
        results = []
        errors = []

        error_summary = {}
        
        for i, raw_config in enumerate(raw_configs):
            try:
                config = direct_config_service.add_config(
                    raw=raw_config,
                    remarks=f"Batch config #{i+1}",
                    added_by=added_by
                )
                
                # Автоматическая синхронизация с Marzban
                if config.auto_sync_to_marzban:
                    try:
                        marzban_integration.sync_direct_config_to_marzban(config)
                    except Exception as e:
                        import logging
                        logging.warning(f"Failed to sync batch config {config.id} to Marzban: {e}")
                
                results.append({
                    "id": config.id,
                    "server": config.server,
                    "port": config.port,
                    "protocol": config.protocol
                })
                
            except Exception as e:
                err_str = str(e)
                if err_str:
                    error_summary[err_str] = error_summary.get(err_str, 0) + 1
                errors.append({
                    "config_index": i,
                    "error": err_str,
                    "raw_prefix": raw_config[:80]
                })
        
        return {
            "total_provided": len(raw_configs),
            "successful_added": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
            "error_summary": error_summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/direct-configs/{config_id}")
async def delete_direct_config(config_id: int, admin: Admin = Depends(Admin.get_current)):
    """Удаление прямой конфигурации"""
    try:
        success = direct_config_service.delete_config(config_id)
        if success:
            return {"message": "Direct config deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Direct config not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/direct-configs/{config_id}/toggle")
async def toggle_direct_config(config_id: int, admin: Admin = Depends(Admin.get_current)):
    """Включение/выключение прямой конфигурации"""
    try:
        config = direct_config_service.toggle_config(config_id)
        if config:
            return {"message": "Direct config toggled successfully", "is_active": config.is_active}
        else:
            raise HTTPException(status_code=404, detail="Direct config not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/direct-configs/{config_id}/sync-to-marzban")
async def sync_direct_config_to_marzban(config_id: int, admin: Admin = Depends(Admin.get_current)):
    """Принудительная синхронизация конкретной конфигурации с Marzban"""
    try:
        config = direct_config_service.get_config_by_id(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Direct config not found")
        
        result = marzban_integration.sync_direct_config_to_marzban(config)
        return {"message": "Config synced to Marzban successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marzban-sync/debug")
async def marzban_sync_debug(admin: Admin = Depends(Admin.get_current)):
    try:
        from app import xray

        inbound_tags = []
        if getattr(xray, "config", None):
            inbound_tags = list(xray.config.inbounds_by_tag.keys())

        host_counts = {}
        try:
            for tag in inbound_tags:
                host_counts[tag] = len(xray.hosts.get(tag, []))
        except Exception:
            host_counts = {}

        return {
            "xray_enabled": bool(getattr(xray, "config", None)),
            "fallback_inbound_tag": config.XRAY_FALLBACKS_INBOUND_TAG,
            "inbound_tags": inbound_tags,
            "host_counts": host_counts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/direct-configs/validate")
async def validate_direct_config(config_data: dict, admin: Admin = Depends(Admin.get_current)):
    """Валидация конфигурации перед добавлением"""
    try:
        raw_config = config_data.get('raw', '')
        if not raw_config:
            raise HTTPException(status_code=400, detail="Raw config is required")
        
        # Парсинг и валидация конфига
        import logging
        logging.info(f"Validating config: {raw_config[:100]}...")
        
        result = checker.process_config(raw_config)
        logging.info(f"Validation result: {result}")
        
        if result:
            return {
                "valid": True,
                "protocol": result["protocol"],
                "server": result["server"],
                "port": result["port"],
                "remarks": result["remarks"],
                "ping_ms": result["ping_ms"],
                "is_active": result["is_active"]
            }
        else:
            return {
                "valid": False,
                "error": "Invalid configuration format - could not parse server/port"
            }
            
    except Exception as e:
        import logging
        logging.error(f"Validation error: {str(e)}")
        return {
            "valid": False,
            "error": str(e)
        }
