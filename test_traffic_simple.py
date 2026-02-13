#!/usr/bin/env python3
"""
Простое тестирование системы мониторинга трафика Xpert Panel
"""

import sys
import os
from datetime import datetime

# Добавляем путь к app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.xpert.traffic_service import traffic_service


def test_traffic_service():
    """Тестирование базового функционала Traffic Service"""
    print("🔧 Testing Traffic Service...")
    
    # Тест записи трафика
    try:
        traffic_service.record_traffic_usage(
            user_token="test_user_123",
            config_server="vpn.example.com",
            config_port=443,
            protocol="vless",
            bytes_uploaded=1024*1024,  # 1MB
            bytes_downloaded=1024*1024*5  # 5MB
        )
        print("✅ Traffic recording test passed")
    except Exception as e:
        print(f"❌ Traffic recording test failed: {e}")
        return False
    
    # Тест записи еще одного трафика
    try:
        traffic_service.record_traffic_usage(
            user_token="test_user_456",
            config_server="another.vpn.com",
            config_port=8443,
            protocol="vmess",
            bytes_uploaded=2*1024*1024,  # 2MB
            bytes_downloaded=10*1024*1024  # 10MB
        )
        print("✅ Second traffic recording test passed")
    except Exception as e:
        print(f"❌ Second traffic recording test failed: {e}")
        return False
    
    # Тест получения статистики пользователя
    try:
        stats = traffic_service.get_user_traffic_stats("test_user_123", 30)
        print(f"✅ User stats test passed: {stats['total_gb_used']:.3f} GB used")
        print(f"   Servers: {len(stats['servers'])}")
        for server in stats['servers']:
            print(f"   - {server['server']}:{server['port']} ({server['protocol']}) - {server['total_gb']:.3f} GB")
    except Exception as e:
        print(f"❌ User stats test failed: {e}")
        return False
    
    # Тест глобальной статистики
    try:
        global_stats = traffic_service.get_global_stats(30)
        print(f"✅ Global stats test passed:")
        print(f"   Total users: {global_stats['total_users']}")
        print(f"   Total servers: {global_stats['total_servers']}")
        print(f"   Total GB used: {global_stats['total_gb_used']:.3f}")
        print(f"   Total connections: {global_stats['total_connections']}")
        print(f"   Top servers: {len(global_stats['top_servers'])}")
    except Exception as e:
        print(f"❌ Global stats test failed: {e}")
        return False
    
    # Тест статистики сервера
    try:
        server_stats = traffic_service.get_server_stats("vpn.example.com", 443, 30)
        print(f"✅ Server stats test passed:")
        print(f"   Unique users: {server_stats['unique_users']}")
        print(f"   Total GB used: {server_stats['total_gb_used']:.3f}")
        print(f"   Total connections: {server_stats['total_connections']}")
    except Exception as e:
        print(f"❌ Server stats test failed: {e}")
        return False
    
    # Тест информации о БД
    try:
        db_info = traffic_service.get_database_info()
        print(f"✅ DB info test passed:")
        print(f"   Database path: {db_info['database_path']}")
        print(f"   Total records: {db_info['total_records']}")
        print(f"   Unique users: {db_info['unique_users']}")
        print(f"   Unique servers: {db_info['unique_servers']}")
        print(f"   Database size: {db_info['database_size_mb']:.2f} MB")
        print(f"   Retention days: {db_info['retention_days']}")
    except Exception as e:
        print(f"❌ DB info test failed: {e}")
        return False
    
    return True


def print_usage_examples():
    """Примеры использования системы"""
    print("\n📚 Traffic Monitoring System Usage Examples:")
    print("=" * 60)
    
    print("\n1. 📡 Webhook вызов от клиента:")
    print("   POST /api/xpert/traffic-webhook")
    print("   Content-Type: application/json")
    print("   Body:")
    webhook_example = """   {
       "user_token": "user123",
       "server": "vpn.example.com", 
       "port": 443,
       "protocol": "vless",
       "bytes_uploaded": 1048576,
       "bytes_downloaded": 2097152
   }"""
    print(webhook_example)
    
    print("\n2. 👤 Статистика пользователя:")
    print("   GET /api/xpert/traffic-stats/user123?days=30")
    print("   Returns: traffic by servers, GB used, connection count")
    
    print("\n3. 🌍 Глобальная статистика:")
    print("   GET /api/xpert/traffic-stats/global?days=30")
    print("   Returns: total users, servers, GB used, top servers")
    
    print("\n4. 🖥️ Статистика для Marzban UI:")
    print("   GET /api/xpert/marzban-traffic-stats?days=30")
    print("   Returns: Marzban-compatible format with external_servers=true")
    
    print("\n5. 🗂️ Очистка старой статистики:")
    print("   POST /api/xpert/traffic-stats/cleanup?days=90")
    print("   Deletes records older than specified days")
    
    print("\n6. 📱 Подписка с отслеживанием:")
    print("   GET /api/xpert/sub?user_token=user123")
    print("   Headers returned:")
    print("   - Traffic-Webhook: https://domain.com/api/xpert/traffic-webhook")
    print("   - User-Token: user123")
    print("   - Subscription-Userinfo: upload=X; download=Y; total=Z; expire=0")
    
    print("\n7. 📊 Информация о базе данных:")
    print("   GET /api/xpert/traffic-stats/database/info")
    print("   Returns: DB size, records count, retention settings")


def print_integration_notes():
    """Заметки по интеграции"""
    print("\n🔗 Integration Notes:")
    print("=" * 40)
    
    print("\n✅ Features implemented:")
    print("   • SQLite database for traffic storage")
    print("   • Middleware for subscription request tracking")
    print("   • Webhook API for traffic data collection")
    print("   • User and global statistics")
    print("   • Marzban UI integration endpoint")
    print("   • Database cleanup functionality")
    print("   • Configuration-based enable/disable")
    
    print("\n🔧 Configuration variables (.env):")
    print("   XPERT_TRAFFIC_TRACKING_ENABLED=True")
    print("   XPERT_TRAFFIC_DB_PATH=data/traffic_stats.db")
    print("   XPERT_TRAFFIC_RETENTION_DAYS=0  # 0 = infinite")
    
    print("\n📈 Traffic flow:")
    print("   1. Client requests subscription with user_token")
    print("   2. Middleware logs the request")
    print("   3. Client sends traffic data to webhook")
    print("   4. Traffic stored in SQLite database")
    print("   5. Statistics available via API")
    print("   6. Marzban UI can fetch external server stats")
    
    print("\n⚡ Performance considerations:")
    print("   • Minimal middleware overhead")
    print("   • SQLite indexes for fast queries")
    print("   • Configurable retention policy")
    print("   • Async API endpoints")


def main():
    """Основная функция тестирования"""
    print("🚀 Xpert Panel Traffic Monitoring System Test")
    print("=" * 50)
    
    # Тестирование сервиса
    service_ok = test_traffic_service()
    
    if not service_ok:
        print("\n❌ Traffic Service tests failed. Please check the implementation.")
        return
    
    print("\n✅ All Traffic Service tests passed!")
    
    # Примеры использования
    print_usage_examples()
    
    # Заметки по интеграции
    print_integration_notes()
    
    print("\n🎯 System ready for production!")
    print("\n📝 Next steps:")
    print("1. 🔄 Restart Xpert Panel to load new middleware")
    print("2. 🧪 Test subscription URLs with tracking")
    print("3. 📱 Implement client-side webhook calls")
    print("4. 🖥️ Add traffic stats to Marzban UI")
    print("5. 📊 Monitor external server usage")


if __name__ == "__main__":
    main()
