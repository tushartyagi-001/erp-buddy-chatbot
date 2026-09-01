from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class StudentOption(BaseModel):
    student_reg_no: int
    label: str


class FileAttachment(BaseModel):
    file_id: str
    filename: str
    label: str
    download_url: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)
    selected_student_reg_no: int | None = None


class ChatResponse(BaseModel):
    reply: str
    reply_type: str = "text"
    options: list[StudentOption] | None = None
    attachments: list[FileAttachment] | None = None


class HealthResponse(BaseModel):
    status: str
    tools_loaded: int


class ChatLimitResetRequest(BaseModel):
    scope: str = Field(
        default="user",
        description="user | branch | all — user=one user+branch, branch=all users in branch, all=entire table",
    )
    user_id: int | None = None
    branch_id: int | None = None
    usage_date: str | None = Field(
        default=None,
        description="YYYY-MM-DD; default today. Ignored when all_dates=true.",
    )
    all_dates: bool = Field(
        default=False,
        description="If true, reset across all dates (not only today).",
    )


class ChatLimitStatusResponse(BaseModel):
    usage_date: str
    user_id: int
    branch_id: int
    used: int
    limit: int
    remaining: int


class ChatLimitResetResponse(BaseModel):
    success: bool
    scope: str
    rows_deleted: int
    message: str
