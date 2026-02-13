import json
import os
import threading
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from app.utils.jwt import get_subscription_payload
from config import XRAY_SUBSCRIPTION_PATH

_storage_file = "data/sub_hwid_locks.json"
_storage_lock = threading.Lock()


def normalize_hwid(hwid: str) -> str:
    return (hwid or "").strip()


def _load_data() -> dict:
    if not os.path.exists(_storage_file):
        return {"locks": {}}
    try:
        with open(_storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"locks": {}}
        if not isinstance(data.get("locks"), dict):
            data["locks"] = {}
        return data
    except Exception:
        return {"locks": {}}


def _save_data(data: dict) -> None:
    os.makedirs(os.path.dirname(_storage_file), exist_ok=True)
    with open(_storage_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_subscription_token(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url.strip())
        parts = [p for p in parsed.path.split("/") if p]
        if not parts:
            return None
        for idx, part in enumerate(parts):
            if part == XRAY_SUBSCRIPTION_PATH and idx + 1 < len(parts):
                token = parts[idx + 1].strip()
                return token or None
    except Exception:
        return None
    return None


def set_required_hwid_for_subscription_url(url: str, hwid: str) -> Optional[str]:
    hwid_norm = normalize_hwid(hwid)
    if not hwid_norm:
        return None

    token = extract_subscription_token(url)
    if not token:
        return None

    payload = get_subscription_payload(token)
    if not payload or not payload.get("username"):
        return None

    username = payload["username"]
    with _storage_lock:
        data = _load_data()
        data["locks"][username] = {
            "hwid": hwid_norm,
            "updated_at": datetime.utcnow().isoformat(),
        }
        _save_data(data)
    return username


def get_required_hwid_for_username(username: str) -> Optional[str]:
    if not username:
        return None
    with _storage_lock:
        data = _load_data()
        item = data.get("locks", {}).get(username)
    if not isinstance(item, dict):
        return None
    hwid = normalize_hwid(item.get("hwid", ""))
    return hwid or None

