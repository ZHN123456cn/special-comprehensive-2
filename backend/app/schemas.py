from datetime import datetime

from pydantic import BaseModel, Field


# ---------- 认证 ----------
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=64, description="密码")


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageResponse(BaseModel):
    message: str


# ---------- 游戏草稿 ----------
class GenerateGameRequest(BaseModel):
    prompt: str = Field(..., min_length=4, max_length=2000, description="游戏需求")


class ReviseGameRequest(BaseModel):
    original_prompt: str = Field(..., min_length=4, max_length=2000)
    current_html: str = Field(..., min_length=100, max_length=400000)
    instruction: str = Field(..., min_length=2, max_length=2000)


class GameDraftResponse(BaseModel):
    title: str
    description: str
    html: str
    generation_ms: int
    model_name: str


class SaveGameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    original_prompt: str = Field(..., min_length=4, max_length=2000)
    description: str = Field(..., min_length=1, max_length=5000)
    html: str = Field(..., min_length=100, max_length=400000)
    generation_ms: int = Field(default=0, ge=0)
    model_name: str = Field(..., min_length=1, max_length=100)


class SaveVersionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=5000)
    html: str = Field(..., min_length=100, max_length=400000)
    change_prompt: str = Field(..., min_length=1, max_length=2000)
    generation_ms: int = Field(default=0, ge=0)
    model_name: str = Field(..., min_length=1, max_length=100)


# ---------- 已保存游戏 ----------
class GameVersionMeta(BaseModel):
    id: int
    version_no: int
    change_prompt: str
    generation_ms: int
    model_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class GameVersionDetail(GameVersionMeta):
    html: str


class GameSummary(BaseModel):
    id: int
    title: str
    description: str
    original_prompt: str
    version_count: int
    latest_version_no: int
    created_at: datetime
    updated_at: datetime


class GameDetail(GameSummary):
    html: str
    versions: list[GameVersionMeta]
