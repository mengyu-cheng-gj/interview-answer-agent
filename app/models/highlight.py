from pydantic import BaseModel, Field
from app.models.candidate import Candidate, TargetJob


class InterviewHighlight(BaseModel):
    point: str = Field(..., min_length=1, description="优势概述")
    evidence: str = Field(..., min_length=1, description="支持优势的真实事实")
    source_project_ids: list[str] = Field(
        ...,
        min_length=1,
        description="证据来源项目 ID",
    )
    matched_requirement: str = Field(
        ...,
        min_length=1,
        description="对应的岗位要求",
    )
    priority: int = Field(
        ...,
        ge=1,
        le=5,
        description="展示优先级，1 为最高",
    )


class HighlightResult(BaseModel):
    candidate_id: str
    highlights: list[InterviewHighlight] = Field(default_factory=list)
    summary: str = Field(default="", description="候选人与岗位的匹配概述")
    missing_information: list[str] = Field(
        default_factory=list,
        description="还需要候选人补充的信息",
    )

class HighlightRequest(BaseModel):
    candidate: Candidate
    target_job: TargetJob