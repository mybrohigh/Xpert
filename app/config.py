import os
from typing import Optional

class Settings:
    # App settings
    APP_NAME: str = "Xpert Panel"
    APP_SHORT_NAME: str = "Xpert"
    VERSION: str = "1.0.0"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DOMAIN: str = os.getenv("DOMAIN", "home.turkmendili.ru")
    
    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Update settings
    UPDATE_INTERVAL_HOURS: int = int(os.getenv("UPDATE_INTERVAL", "1"))
    
    # Ping settings
    MAX_PING_MS: int = int(os.getenv("MAX_PING_MS", "300"))
    PING_TIMEOUT: int = int(os.getenv("PING_TIMEOUT", "3"))
    MAX_CONFIGS: int = int(os.getenv("MAX_CONFIGS", "100"))
    
    # Target IPs for ping check (configs must be reachable from these IPs)
    # These are the user's network IPs that will use the VPN
    TARGET_CHECK_IPS: list = os.getenv("TARGET_CHECK_IPS", "93.171.220.198,185.69.186.175").split(",")
    
    # Data directory
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")

settings = Settings()
