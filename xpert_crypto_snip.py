        # Формат ответа совместимый с Marzban
        return {
            "users_traffic": {
                **global_stats,
                "external_servers": True,  # Флаг что это внешние сервера
                "integration_type": "xpert",
                "data_source": "traffic_monitoring_system"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get marzban traffic stats: {e}")
        return {
            "users_traffic": {
                "total_users": 0,
                "total_servers": 0,
                "total_gb_used": 0,
                "total_connections": 0,
                "external_servers": False,
                "integration_type": "xpert_error",
                "error": str(e)
            }
        }

@router.post("/crypto-link")
async def create_crypto_link(
    data: CryptoLinkRequest,
    admin: Admin = Depends(Admin.get_current),
    db: Session = Depends(get_db),
):
    try:
        payload = {"url": data.url.strip()}

        hwid_value = (data.hwid or "").strip()
        hwid_limit = data.hwid_limit

        if hwid_limit is not None and not (1 <= int(hwid_limit) <= 5):
            raise HTTPException(status_code=400, detail="HWID limit must be in range 1..5")

        # For HWID options we must be able to parse and validate THIS panel /sub token.
        username_from_url = None
        if hwid_value or (hwid_limit is not None) or (not admin.is_sudo):
            try:
                from app.xpert.hwid_lock_service import extract_subscription_token
                from app.utils.jwt import get_subscription_payload

                token = extract_subscription_token(payload["url"])
                sub = get_subscription_payload(token) if token else None
                username_from_url = sub.get("username") if sub else None
            except Exception:
                username_from_url = None

        # sudo=n: can encrypt ONLY own Marzban /sub link from this panel (with or without HWID options)
        if not admin.is_sudo:
            if not username_from_url:
                raise HTTPException(status_code=403, detail="Only this panel Marzban /sub links are allowed")

            dbuser = crud.get_user(db, username_from_url)
            if not dbuser or not getattr(dbuser, "admin", None) or dbuser.admin.username != admin.username:
                raise HTTPException(status_code=403, detail="You are not allowed")

        # Apply HWID options (sudo=y or allowed sudo=n only)
        if hwid_value:
            username = set_required_hwid_for_subscription_url(payload["url"], hwid_value)
            if not username:
                raise HTTPException(status_code=400, detail="HWID mode requires a valid Marzban /sub URL")
            payload["hwid"] = hwid_value

        if hwid_limit is not None:
            username = set_hwid_limit_for_subscription_url(payload["url"], int(hwid_limit), hwid_value)
            if not username:
                raise HTTPException(status_code=400, detail="HWID limit mode requires a valid Marzban /sub URL")

        resp = requests.post("https://crypto.happ.su/api-v2.php", json=payload, timeout=15)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                j = resp.json()
                if isinstance(j, str):
                    return {"link": j}
                if isinstance(j, dict):
                    for key in ("url", "link", "result", "data", "encrypted", "encrypted_link"):
                        if key in j and isinstance(j[key], str):
                            return {"link": j[key]}
                    return j
            except Exception:
                pass

        text = resp.text.strip()
        return {"link": text}
    except HTTPException:
        raise
    except Exception:
        logger.exception("crypto-link failed")
        raise HTTPException(status_code=502, detail="Crypto link generation failed")
