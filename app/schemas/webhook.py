from pydantic import BaseModel, Field


class MetaInfo(BaseModel):
    title: str
    problem_id: str
    link: str | None = None
    level: str | None = None
    language: str


class SubmissionInfo(BaseModel):
    code: str
    memory: int | None = None
    time: int | None = None


class NotionSettings(BaseModel):
    token: str
    database_id: str


class WebhookPayload(BaseModel):
    platform: str = Field(..., description="ex) baekjoon, programmers")
    meta_info: MetaInfo
    submission_info: SubmissionInfo
    notion_settings: NotionSettings | None = None
