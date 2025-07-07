# routers/update.py

from fastapi import APIRouter, Request
from fastapi.responses import Response

router = APIRouter()

# 글로벌 설정값
left_value = 17
right_value = 17
distorted = False

@router.post("/update")
async def update(request: Request):
    global left_value, right_value, distorted

    form = await request.body()
    params = dict(x.split("=") for x in form.decode().split("&"))

    left_value = int(params.get("left", left_value))
    right_value = int(params.get("right", right_value))
    distorted = params.get("distorted", "false").lower() == "true"

    print(f" Updated: left={left_value}, right={right_value}, distorted={distorted}")
    return Response(content="Values updated")

def get_settings():
    return left_value, right_value, distorted
