"""兼容早期的可选路由；当前主入口集中定义于 app.main。"""
from fastapi import APIRouter, Request
from app.models.interaction import InteractionRequest, InteractionResponse

router = APIRouter()


@router.post("/revise", response_model=InteractionResponse)
async def revise(body: InteractionRequest, request: Request):
    from app.main import interact
    return await interact(body, request)
