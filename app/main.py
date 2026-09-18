from app.services.cache_service import CacheService
from app.models.candidate import Candidate, TargetJob
import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.exceptions import OutputParserException

from app.chains.answer_chain import AnswerChain
from app.chains.highlight_chain import HighlightChain
from app.chains.interaction_chain import InteractionChain

from app.models.answer import AnswerRequest, AnswerResponse
from app.models.highlight import HighlightRequest, HighlightResult
from app.models.interaction import (
    InteractionRequest,
    InteractionResponse,
)


logger = logging.getLogger("interview_agent")


# ---------- 服务初始化 ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建 Chain。
    # 如果缺少模型配置，启动会直接报错，提醒补充配置。
    app.state.highlight_chain = HighlightChain()
    app.state.answer_chain = AnswerChain()
    app.state.interaction_chain = InteractionChain()

    app.state.cache = CacheService()
    try:
        yield
    finally:
        await app.state.cache.close()


app = FastAPI(
    title="Interview Answer Agent",
    description="中英文面试亮点提取、回答生成与互动修改接口",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------- 公共辅助函数 ----------

async def get_or_extract_highlights(
    request: Request, candidate: Candidate, target_job: TargetJob,
) -> HighlightResult:
    project_ids = [p.project_id for p in candidate.projects]
    if len(project_ids) != len(set(project_ids)):
        raise HTTPException(status_code=422, detail="候选人的 project_id 不能重复")
    cache: CacheService = request.app.state.cache
    cached = await cache.get_highlights(candidate, target_job)
    if cached is not None:
        return cached
    result = await request.app.state.highlight_chain.extract(candidate, target_job)
    await cache.set_highlights(candidate, target_job, result)
    return result


def validate_projects(answer_request: AnswerRequest) -> None:
    """检查项目 ID，避免调用模型后才发现重复。"""
    project_ids = [
        project.project_id
        for project in answer_request.candidate.projects
    ]

    if len(project_ids) != len(set(project_ids)):
        raise HTTPException(
            status_code=422,
            detail="候选人的 project_id 不能重复",
        )


def model_error_message(error: Exception) -> str:
    """返回适合客户端展示的错误信息。"""
    if isinstance(error, (OutputParserException, ValueError)):
        return "生成结果未通过格式或业务校验，请检查输入或重新生成。"

    return "模型服务调用失败，请检查服务配置、网络或稍后重试。"


def log_failure(operation: str, error: Exception) -> None:
    # 不直接记录异常正文，避免其中包含候选人资料或模型输出。
    logger.error(
        "%s失败，异常类型：%s",
        operation,
        type(error).__name__,
    )


def encode_sse(event: str, data: dict) -> str:
    """将事件编码成 SSE 文本。"""
    payload = json.dumps(data, ensure_ascii=False)

    return f"event: {event}\ndata: {payload}\n\n"


# ---------- 健康检查 ----------

@app.get("/health", tags=["health"])
async def health():
    # 仅说明 API 已启动，不代表上游模型一定可用。
    return {"status": "ok"}


# ---------- 面试亮点提取 ----------

@app.post(
    "/api/highlight/extract",
    response_model=HighlightResult,
    tags=["highlight"],
)
async def extract_highlights(
    body: HighlightRequest,
    request: Request,
):
    project_ids = [
        project.project_id
        for project in body.candidate.projects
    ]

    if len(project_ids) != len(set(project_ids)):
        raise HTTPException(
            status_code=422,
            detail="候选人的 project_id 不能重复",
        )


    try:
        return await get_or_extract_highlights(
            request=request,
            candidate=body.candidate,
            target_job=body.target_job,
        )
    except Exception as error:
        log_failure("亮点提取", error)

        raise HTTPException(
            status_code=502,
            detail=model_error_message(error),
        ) from error


# ---------- 完整回答生成 ----------

@app.post(
    "/api/answer/generate",
    response_model=AnswerResponse,
    tags=["answer"],
)
async def generate_answer(
    body: AnswerRequest,
    request: Request,
):
    validate_projects(body)

    answer_chain: AnswerChain = request.app.state.answer_chain

    try:
        # 第一步：提炼与岗位相关的亮点
        highlights = await get_or_extract_highlights(
            request=request,
            candidate=body.candidate,
            target_job=body.target_job,
        )

        # 第二步：生成并校验回答
        return await answer_chain.generate(
            request=body,
            highlights=highlights,
        )

    except Exception as error:
        log_failure("回答生成", error)

        raise HTTPException(
            status_code=502,
            detail=model_error_message(error),
        ) from error


# ---------- SSE 分阶段返回 ----------

@app.post(
    "/api/answer/stream",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "返回 status、highlights、done 或 error 事件",
            "content": {
                "text/event-stream": {
                    "schema": {"type": "string"}
                }
            },
        }
    },
    tags=["answer"],
)
async def stream_answer(
    body: AnswerRequest,
    request: Request,
):
    # 在开始 SSE 响应前检查输入。
    validate_projects(body)

    answer_chain: AnswerChain = request.app.state.answer_chain

    async def event_generator():
        started_at = time.perf_counter()

        try:
            yield encode_sse(
                "status",
                {
                    "stage": "extracting_highlights",
                    "message": "正在提取面试亮点",
                },
            )

            highlights = await get_or_extract_highlights(
                request=request,
                candidate=body.candidate,
                target_job=body.target_job,
            )

            if await request.is_disconnected():
                return

            yield encode_sse(
                "highlights",
                highlights.model_dump(mode="json"),
            )

            yield encode_sse(
                "status",
                {
                    "stage": "generating_answer",
                    "message": "正在生成并校验面试回答",
                },
            )

            answer = await answer_chain.generate(
                request=body,
                highlights=highlights,
            )

            if await request.is_disconnected():
                return

            elapsed = time.perf_counter() - started_at

            yield encode_sse(
                "done",
                {
                    "answer": answer.model_dump(mode="json"),
                    "elapsed_seconds": round(elapsed, 2),
                },
            )

        except asyncio.CancelledError:
            # 客户端断开或请求被取消时，继续传播取消信号。
            raise

        except Exception as error:
            log_failure("流式回答生成", error)

            # SSE 已开始后，通过 error 事件告知失败。
            # 此时不能再改成普通 HTTP 502 响应。
            yield encode_sse(
                "error",
                {
                    "message": model_error_message(error),
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------- 互动回复 ----------

@app.post(
    "/api/interaction/reply",
    response_model=InteractionResponse,
    tags=["interaction"],
)
async def interact(
    body: InteractionRequest,
    request: Request,
):
    validate_projects(body.original)

    chain: InteractionChain = request.app.state.interaction_chain

    try:
        return await chain.reply(body)

    except Exception as error:
        log_failure("互动回复", error)

        raise HTTPException(
            status_code=502,
            detail=model_error_message(error),
        ) from error