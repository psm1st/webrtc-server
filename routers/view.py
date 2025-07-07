from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from routers.update import get_settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    left_value, right_value, distorted = get_settings()
    adjusted_left = -left_value + (17 if distorted else 0)
    adjusted_right = -right_value + (17 if distorted else 0)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "left_value": adjusted_left,
        "right_value": adjusted_right
    })
