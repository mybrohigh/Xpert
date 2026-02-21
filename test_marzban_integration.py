#!/usr/bin/env python3
"""
Тестирование интеграции системы мониторинга трафика с Marzban
"""

import sys
import os
from datetime import datetime

# Добавляем путь к app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.xpert.traffic_service import traffic_service


def test_admin_integration():
    """Тестирование функций интеграции с админами"""
    print("🔧 Testing Marzban Integration...")
    
    # Тест записи трафика для разных пользователей
    test_users = [
        ("admin1", "server1.vpn.com", 443, "vless", 1024*1024, 5*1024*1024),
        ("admin1", "server2.vpn.com", 8443, "vmess", 2*1024*1024, 8*1024*1024),
        ("admin2", "server3.vpn.com", 443, "trojan", 3*1024*1024, 12*1024*1024),
    ]
    
    try:
        for user_token, server, port, protocol, upload, download in test_users:
            traffic_service.record_traffic_usage(
                user_token=user_token,
                config_server=server,
                config_port=port,
                protocol=protocol,
                bytes_uploaded=upload,
                bytes_downloaded=download
            )
            print(f"✅ Recorded traffic for {user_token}: {server}:{port}")
        
        print("✅ Traffic recording for multiple users passed")
    except Exception as e:
        print(f"❌ Traffic recording failed: {e}")
        return False
    
    # Тест получения статистики админа
    try:
        admin1_stats = traffic_service.get_admin_traffic_usage("admin1", 30)
        print(f"✅ Admin1 stats: {admin1_stats['external_traffic_gb']:.3f} GB")
        print(f"   Unique users: {admin1_stats['external_unique_users']}")
        print(f"   Unique servers: {admin1_stats['external_unique_servers']}")
        
        admin2_stats = traffic_service.get_admin_traffic_usage("admin2", 30)
        print(f"✅ Admin2 stats: {admin2_stats['external_traffic_gb']:.3f} GB")
    except Exception as e:
        print(f"❌ Admin stats test failed: {e}")
        return False
    
    # Тест проверки лимита
    try:
        limit_check_10gb = traffic_service.check_admin_traffic_limit("admin1", 10*1024**3)  # 10GB
        print(f"✅ Limit check (10GB): {limit_check_10gb['used_gb']:.3f}/{limit_check_10gb['limit_gb']:.3f} GB "
              f"({limit_check_10gb['percentage_used']}% used)")
        
        limit_check_unlimited = traffic_service.check_admin_traffic_limit("admin2", 0)  # Без лимита
        print(f"✅ Unlimited check: {limit_check_unlimited['within_limit']}")
    except Exception as e:
        print(f"❌ Limit check test failed: {e}")
        return False
    
    return True


def test_reset_functionality():
    """Тестирование функций сброса"""
    print("\n🔄 Testing Reset Functionality...")
    
    try:
        # Получаем статистику перед сбросом
        before_stats = traffic_service.get_admin_traffic_usage("admin1", 30)
        before_gb = before_stats['external_traffic_gb']
        print(f"📊 Before reset: {before_gb:.3f} GB")
        
        # Сбрасываем трафик
        reset_result = traffic_service.reset_admin_external_traffic("admin1")
        print(f"✅ Reset result: {reset_result['status']}")
        print(f"   Cleared: {reset_result['reset_gb']:.3f} GB")
        print(f"   Connections: {reset_result['reset_connections']}")
        
        # Проверяем что после сброса статистика пустая
        after_stats = traffic_service.get_admin_traffic_usage("admin1", 30)
        after_gb = after_stats['external_traffic_gb']
        print(f"📊 After reset: {after_gb:.3f} GB")
        
        if after_gb == 0:
            print("✅ Reset functionality working correctly")
        else:
            print("❌ Reset failed - traffic not cleared")
            return False
            
    except Exception as e:
        print(f"❌ Reset test failed: {e}")
        return False
    
    return True


def test_combined_scenarios():
    """Тестирование комбинированных сценариев"""
    print("\n🎯 Testing Combined Scenarios...")
    
    # Добавляем трафик для admin3
    try:
        traffic_service.record_traffic_usage(
            user_token="admin3",
            config_server="test.vpn.com",
            config_port=443,
            protocol="vless",
            bytes_uploaded=5*1024*1024,
            bytes_downloaded=15*1024*1024
        )
        
        # Проверяем с лимитом 20GB
        limit_check = traffic_service.check_admin_traffic_limit("admin3", 20*1024**3)
        print(f"✅ Admin3 with 20GB limit: {limit_check['used_gb']:.3f}/{limit_check['limit_gb']:.3f} GB "
              f"({limit_check['percentage_used']}% used)")
        
        if not limit_check['within_limit']:
            print("⚠️  Admin3 exceeded limit!")
        
        # Тест статистики после превышения лимита
        admin3_stats = traffic_service.get_admin_traffic_usage("admin3", 30)
        print(f"✅ Admin3 detailed stats: {admin3_stats['external_traffic_gb']:.3f} GB")
        
    except Exception as e:
        print(f"❌ Combined scenario test failed: {e}")
        return False
    
    return True


def print_integration_examples():
    """Примеры использования интеграции"""
    print("\n📚 Marzban Integration Examples:")
    print("=" * 50)
    
    print("\n1. 🔄 Сброс всего трафика (Marzban + внешний):")
    print("   POST /api/admin/usage/reset/admin1")
    print("   - Сбрасывает users_usage в Marzban")
    print("   - Сбрасывает внешний трафик в Xpert")
    
    print("\n2. 📊 Получение общего использования:")
    print("   GET /api/admin/usage/admin1")
    print("   - Возвращает: Marzban_usage + External_traffic (в байтах)")
    
    print("\n3. 📈 Детальная статистика:")
    print("   GET /api/admin/usage/admin1/detailed")
    print("   Returns:")
    detailed_example = """   {
       "username": "admin1",
       "marzban_usage_bytes": 1073741824,
       "marzban_usage_gb": 1.000,
       "external_traffic": {
           "external_traffic_gb": 2.456,
           "external_unique_users": 15,
           "external_unique_servers": 8
       },
       "total_usage_bytes": 3640646656,
       "traffic_limit_bytes": 10737418240,
       "traffic_limit_gb": 10.000,
       "limit_check": {
           "within_limit": false,
           "percentage_used": 33.9
       }
   }"""
    print(detailed_example)
    
    print("\n4. 🗑️ Сброс только внешнего трафика:")
    print("   POST /api/admin/external-traffic/reset/admin1")
    print("   - Сбрасывает только внешний трафик")
    print("   - Не затрагивает Marzban users_usage")
    
    print("\n5. 📊 Статистика только внешнего трафика:")
    print("   GET /api/admin/external-traffic/stats/admin1?days=30")
    print("   Returns:")
    external_example = """   {
       "admin_username": "admin1",
       "external_traffic_gb": 2.456,
       "external_unique_users": 15,
       "external_unique_servers": 8,
       "traffic_limit_bytes": 10737418240,
       "traffic_limit_gb": 10.000,
       "limit_check": {
           "within_limit": false,
           "percentage_used": 24.6
       }
   }"""
    print(external_example)
    
    print("\n6. 🎯 Проверка лимитов в UI:")
    limit_ui_example = """   Marzban UI может использовать:
   - Кнопка "Сбросить трафик" → /api/admin/usage/reset/{username}
   - Кнопка "Лимит трафика" → traffic_limit в админах
   - Индикатор использования → total_usage с учетом внешнего трафика
   - Предупреждения → когда limit_check.percentage_used > 80%"""
    print(limit_ui_example)


def print_api_summary():
    """Сводка новых API эндпоинтов"""
    print("\n🔗 New API Endpoints:")
    print("=" * 30)
    
    endpoints = [
        ("POST /api/admin/usage/reset/{username}", "Сброс всего трафика"),
        ("GET /api/admin/usage/{username}", "Общее использование (Marzban + внешний)"),
        ("GET /api/admin/usage/{username}/detailed", "Детальная статистика"),
        ("POST /api/admin/external-traffic/reset/{username}", "Сброс только внешнего трафика"),
        ("GET /api/admin/external-traffic/stats/{username}", "Статистика внешнего трафика")
    ]
    
    for endpoint, description in endpoints:
        print(f"   {endpoint:<45} - {description}")


def main():
    """Основная функция тестирования"""
    print("🚀 Marzban Integration Test Suite")
    print("=" * 40)
    
    # Тестирование базовой интеграции
    integration_ok = test_admin_integration()
    
    # Тестирование сброса
    reset_ok = test_reset_functionality()
    
    # Тестирование комбинированных сценариев
    combined_ok = test_combined_scenarios()
    
    # Примеры использования
    print_integration_examples()
    
    # Сводка API
    print_api_summary()
    
    # Итог
    print("\n🎯 Integration Test Results:")
    print("=" * 30)
    print(f"Admin Integration: {'✅ PASS' if integration_ok else '❌ FAIL'}")
    print(f"Reset Functionality: {'✅ PASS' if reset_ok else '❌ FAIL'}")
    print(f"Combined Scenarios: {'✅ PASS' if combined_ok else '❌ FAIL'}")
    
    if integration_ok and reset_ok and combined_ok:
        print("\n🎉 All tests passed! Marzban integration ready!")
        print("\n📝 Next steps:")
        print("1. 🔄 Перезапустите Xpert")
        print("2. 🖥️  Откройте Marzban UI")
        print("3. 🎯 Протестируйте кнопки 'Сбросить трафик' и 'Лимит трафика'")
        print("4. 📊 Проверьте что внешний трафик учитывается")
        print("5. ✅ Убедитесь что лимиты работают корректно")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
    
    print("\n📚 Documentation: TRAFFIC_MONITORING_GUIDE.md")


if __name__ == "__main__":
    main()
