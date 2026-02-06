from fastapi import APIRouter
from fastapi.responses import HTMLResponse, PlainTextResponse

from config import HOME_PAGE_TEMPLATE
from app.templates import render_template
from app.xpert.service import xpert_service

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def base():
    return render_template(HOME_PAGE_TEMPLATE)


@router.get("/sub")
async def public_subscription(format: str = "universal"):
    content = xpert_service.generate_subscription(format)

    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Profile-Update-Interval": "1",
        "Subscription-Userinfo": "upload=0; download=0; total=0; expire=0",
        "Profile-Title": "Xpert Panel"
    }

    return PlainTextResponse(content=content, headers=headers)