from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional
import requests

from app.xpert.service import xpert_service
from app.xpert.marzban_integration import marzban_integration
from app.xpert.ping_stats import ping_stats_service
from app.xpert.direct_config_service import direct_config_service
from app.xpert.checker import checker
from app.xpert.hwid_lock_service import set_required_hwid_for_subscription_url, set_hwid_limit_for_subscription_url
from app.models.admin import Admin
from app.db import Session, crud, get_db
import config
from app import logger

router = APIRouter(prefix="/xpert", tags=["Xpert"])


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
