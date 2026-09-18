from enum import Enum

from pydantic import BaseModel, Field, model_validator

from app.models.candidate import Candidate, TargetJob


class LanguageType(str, Enum):
    ZH = "zh"
    EN = "en"
    BOTH = "both"


class QuestionType(str, Enum):
    SELF_INTRODUCTION = "self_introduction"  # 自我介绍
    PROJECT = "project"                    # 项目经历
    TECHNICAL = "technical"                # 技术原理
    BEHAVIORAL = "behavioral"              # 行为面试
    CAREER = "career"                      # 职业规划
    OTHER = "other"


class StyleType(str, Enum):
    NATURAL = "natural"        # 自然口语
    PROFESSIONAL = "professional"  # 专业正式
    CONCISE = "concise"        # 简洁直接


class AnswerRequest(BaseModel):
    candidate: Candidate
    target_job: TargetJob

    question: str = Field(
        ...,
        min_length=1,
        max_length=3000,
        description="面试问题",
    )
    question_type: QuestionType | None = Field(
        default=None,
        description="不传时由业务层识别题型",
    )
    language: LanguageType = LanguageType.BOTH
    style: StyleType = StyleType.NATURAL
    duration_seconds: int = Field(
        default=120,
        ge=30,
        le=600,
        description="每种语言回答的目标时长",
    )


class AnswerContent(BaseModel):
    outline: list[str] = Field(
        default_factory=list,
        description="回答提纲",
    )
    content: str = Field(..., min_length=1, description="适合口述的完整回答")
    estimated_duration_seconds: int | None = Field(
        default=None,
        ge=1,
        description="业务层估算的口述时长",
    )


class AnswerEvidence(BaseModel):
    project_id: str = Field(..., min_length=1, description="来源项目 ID")
    fact: str = Field(..., min_length=1, description="本次回答使用的项目事实")


class AnswerResponse(BaseModel):
    question_type: QuestionType
    language: LanguageType
    style: StyleType

    zh: AnswerContent | None = None
    en: AnswerContent | None = None

    evidence: list[AnswerEvidence] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    requires_review: bool = Field(
        default=True,
        description="是否需要人工确认",
    )

    @model_validator(mode="after")
    def check_language_content(self) -> "AnswerResponse":
        if self.language in (LanguageType.ZH, LanguageType.BOTH):
            if self.zh is None:
                raise ValueError("请求中文回答时，zh 不能为空")

        if self.language in (LanguageType.EN, LanguageType.BOTH):
            if self.en is None:
                raise ValueError("请求英文回答时，en 不能为空")

        if self.language == LanguageType.ZH and self.en is not None:
            raise ValueError("仅请求中文时，不应返回英文内容")

        if self.language == LanguageType.EN and self.zh is not None:
            raise ValueError("仅请求英文时，不应返回中文内容")

        return self