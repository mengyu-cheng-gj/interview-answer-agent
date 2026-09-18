"""兼容早期的可选路由；当前主入口集中定义于 app.main。"""
from fastapi import APIRouter, Request
from app.models.answer import AnswerRequest, AnswerResponse

router = APIRouter()


@router.post("/generate", response_model=AnswerResponse)
async def generate(body: AnswerRequest, request: Request):
    from app.main import generate_answer
    return await generate_answer(body, request)
