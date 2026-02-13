#!/usr/bin/env python3
"""
Тестирование системы мониторинга трафика Xpert Panel
"""

import sys
import os
import json
import asyncio
import aiohttp
from datetime import datetime

# Добавляем путь к app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.xpert.traffic_service import traffic_service


async def test_traffic_service():
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
    
    # Тест получения статистики пользователя
    try:
        stats = traffic_service.get_user_traffic_stats("test_user_123", 30)
        print(f"✅ User stats test passed: {stats['total_gb_used']} GB used")
    except Exception as e:
        print(f"❌ User stats test failed: {e}")
        return False
    
    # Тест глобальной статистики
    try:
        global_stats = traffic_service.get_global_stats(30)
        print(f"✅ Global stats test passed: {global_stats['total_users']} users, {global_stats['total_gb_used']} GB")
    except Exception as e:
        print(f"❌ Global stats test failed: {e}")
        return False
    
    # Тест информации о БД
    try:
        db_info = traffic_service.get_database_info()
        print(f"✅ DB info test passed: {db_info['total_records']} records, {db_info['database_size_mb']} MB")
    except Exception as e:
        print(f"❌ DB info test failed: {e}")
        return False
    
    return True


async def test_api_endpoints(base_url="http://localhost:8000"):
    """Тестирование API эндпоинтов"""
    print(f"\n🌐 Testing API endpoints at {base_url}...")
    
    async with aiohttp.ClientSession() as session:
        # Тест webhook
        webhook_data = {
            "user_token": "test_user_456",
            "server": "test.vpn.com",
            "port": 443,
            "protocol": "vmess",
            "bytes_uploaded": 2048,
            "bytes_downloaded": 4096
        }
        
        try:
            async with session.post(f"{base_url}/api/xpert/traffic-webhook", 
                               json=webhook_data) as resp:
                if resp.status == 200:
                    print("✅ Webhook test passed")
                else:
                    print(f"❌ Webhook test failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"❌ Webhook test error: {e}")
            return False
        
        # Тест статистики пользователя
        try:
            async with session.get(f"{base_url}/api/xpert/traffic-stats/test_user_456") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ User stats API test passed: {data.get('total_gb_used', 0)} GB")
                else:
                    print(f"❌ User stats API test failed: {resp.status}")
        except Exception as e:
            print(f"❌ User stats API test error: {e}")
        
        # Тест глобальной статистики
        try:
            async with session.get(f"{base_url}/api/xpert/traffic-stats/global") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Global stats API test passed: {data.get('total_users', 0)} users")
                else:
                    print(f"❌ Global stats API test failed: {resp.status}")
        except Exception as e:
            print(f"❌ Global stats API test error: {e}")
        
        # Тест информации о БД
        try:
            async with session.get(f"{base_url}/api/xpert/traffic-stats/database/info") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ DB info API test passed: {data.get('total_records', 0)} records")
                else:
                    print(f"❌ DB info API test failed: {resp.status}")
        except Exception as e:
            print(f"❌ DB info API test error: {e}")
        
        # Тест Marzban интеграции
        try:
            async with session.get(f"{base_url}/api/xpert/marzban-traffic-stats") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    external = data.get('users_traffic', {}).get('external_servers', False)
                    print(f"✅ Marzban integration test passed: external_servers={external}")
                else:
                    print(f"❌ Marzban integration test failed: {resp.status}")
        except Exception as e:
            print(f"❌ Marzban integration test error: {e}")
    
    return True


async def test_subscription_endpoints(base_url="http://localhost:8000"):
    """Тестирование подписных эндпоинтов"""
    print(f"\n📱 Testing subscription endpoints at {base_url}...")
    
    async with aiohttp.ClientSession() as session:
        # Тест базовой подписки
        try:
            async with session.get(f"{base_url}/api/xpert/sub?user_token=test_user_789") as resp:
                if resp.status == 200:
                    headers = dict(resp.headers)
                    webhook_url = headers.get('Traffic-Webhook', '')
                    user_token = headers.get('User-Token', '')
                    print(f"✅ Subscription endpoint test passed")
                    print(f"   Webhook URL: {webhook_url}")
                    print(f"   User Token: {user_token}")
                else:
                    print(f"❌ Subscription endpoint test failed: {resp.status}")
        except Exception as e:
            print(f"❌ Subscription endpoint test error: {e}")
        
        # Тест direct configs подписки
        try:
            async with session.get(f"{base_url}/api/xpert/direct-configs/sub?user_token=test_user_789") as resp:
                if resp.status == 200:
                    headers = dict(resp.headers)
                    webhook_url = headers.get('Traffic-Webhook', '')
                    user_token = headers.get('User-Token', '')
                    print(f"✅ Direct subscription endpoint test passed")
                    print(f"   Webhook URL: {webhook_url}")
                    print(f"   User Token: {user_token}")
                else:
                    print(f"❌ Direct subscription endpoint test failed: {resp.status}")
        except Exception as e:
            print(f"❌ Direct subscription endpoint test error: {e}")


def print_usage_examples():
    """Примеры использования системы"""
    print("\n📚 Usage Examples:")
    print("=" * 50)
    
    print("\n1. Webhook вызов от клиента:")
    webhook_example = {
        "user_token": "user123",
        "server": "vpn.example.com",
        "port": 443,
        "protocol": "vless",
        "bytes_uploaded": 1048576,
        "bytes_downloaded": 2097152
    }
    print(json.dumps(webhook_example, indent=2))
    
    print("\n2. Получение статистики пользователя:")
    print("GET /api/xpert/traffic-stats/user123?days=30")
    
    print("\n3. Получение глобальной статистики:")
    print("GET /api/xpert/traffic-stats/global?days=30")
    
    print("\n4. Статистика для Marzban UI:")
    print("GET /api/xpert/marzban-traffic-stats?days=30")
    
    print("\n5. Очистка старой статистики:")
    print("POST /api/xpert/traffic-stats/cleanup?days=90")
    
    print("\n6. Подписка с отслеживанием:")
    print("GET /api/xpert/sub?user_token=user123")
    print("Headers: Traffic-Webhook, User-Token")


async def main():
    """Основная функция тестирования"""
    print("🚀 Xpert Panel Traffic Monitoring System Test")
    print("=" * 50)
    
    # Тестирование сервиса
    service_ok = await test_traffic_service()
    
    if not service_ok:
        print("\n❌ Traffic Service tests failed. Please check the implementation.")
        return
    
    # Тестирование API (требует запущенного сервера)
    try:
        await test_api_endpoints()
    except Exception as e:
        print(f"\n⚠️  API tests skipped (server not running): {e}")
    
    # Тестирование подписных эндпоинтов
    try:
        await test_subscription_endpoints()
    except Exception as e:
        print(f"\n⚠️  Subscription tests skipped (server not running): {e}")
    
    # Примеры использования
    print_usage_examples()
    
    print("\n✅ Testing completed!")
    print("\n📝 Next steps:")
    print("1. Start the Xpert Panel server")
    print("2. Test subscription URLs with tracking")
    print("3. Implement client-side webhook calls")
    print("4. Monitor traffic in Marzban UI")


if __name__ == "__main__":
    asyncio.run(main())
