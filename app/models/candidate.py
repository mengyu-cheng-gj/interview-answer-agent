from pydantic import BaseModel, Field


class ProjectExperience(BaseModel):
    project_id: str = Field(..., min_length=1, description="项目唯一 ID")
    name: str = Field(..., min_length=1, description="项目名称")
    background: str = Field(..., min_length=1, description="项目背景和目标")
    role: str = Field(..., min_length=1, description="候选人的个人职责")

    tech_stack: list[str] = Field(
        default_factory=list,
        description="实际使用过的技术",
    )
    actions: list[str] = Field(
        default_factory=list,
        description="候选人实际完成的工作",
    )
    results: list[str] = Field(
        default_factory=list,
        description="真实结果；没有量化指标时不要编造",
    )


class Candidate(BaseModel):
    candidate_id: str = Field(..., min_length=1, description="候选人 ID")
    name: str = Field(..., min_length=1, description="姓名或昵称")
    education: str | None = Field(default=None, description="教育背景")
    years_of_experience: float | None = Field(
        default=None,
        ge=0,
        description="工作年限；未知时不填",
    )
    skills: list[str] = Field(
        default_factory=list,
        description="候选人提供的技能",
    )
    projects: list[ProjectExperience] = Field(
        default_factory=list,
        description="真实项目经历",
    )


class TargetJob(BaseModel):
    title: str = Field(..., min_length=1, description="目标岗位")
    company: str | None = Field(default=None, description="目标公司")
    description: str = Field(default="", description="岗位 JD")
    requirements: list[str] = Field(
        default_factory=list,
        description="岗位核心要求",
    )
