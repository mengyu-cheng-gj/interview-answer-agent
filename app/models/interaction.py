from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from app.models.answer import AnswerRequest, AnswerResponse


class IntentType(str, Enum):
    FOLLOW_UP = "follow_up"          # 回答面试官追问
    SHORTEN = "shorten"              # 缩短回答
    EXPAND = "expand"                # 展开细节
    TRANSLATE = "translate"          # 转换语言
    CHANGE_STYLE = "change_style"    # 修改表达风格
    EXPLAIN = "explain"              # 解释回答中的概念
    OTHER = "other"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=20000)


class InteractionRequest(BaseModel):
    original: AnswerRequest = Field(
        ...,
        description="原始资料和生成设置",
    )
    previous_answer: AnswerResponse = Field(
        ...,
        description="上一次生成的回答",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=3000,
        description="追问或修改要求",
    )
    context: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
        description="最近的对话记录",
    )


class InteractionResponse(BaseModel):
    intent: IntentType
    reply: str = Field(..., min_length=1, description="对用户请求的说明")
    updated_answer: AnswerResponse | None = Field(
        default=None,
        description="生成新版本时返回；仅解释概念时可为空",
    )
    clarification_questions: list[str] = Field(
        default_factory=list,
        description="信息不足时需要向用户确认的问题",
    )