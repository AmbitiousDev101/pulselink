from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID


class URLSubmit(BaseModel):
    url: str = Field(..., description="The URL to analyze", examples=["https://example.com"])


class URLResult(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    redirect_chain: list[str] = []
    ssl_valid: Optional[bool] = None
    ssl_expires_at: Optional[str] = None
    tech_stack: list[str] = []
    safety_score: Optional[str] = None
    screenshot_url: Optional[str] = None
    analyzed_at: Optional[str] = None


class URLResponse(BaseModel):
    id: UUID
    url: str
    url_hash: str
    status: str
    created_at: datetime
    result: Optional[URLResult] = None


class URLSubmitResponse(BaseModel):
    job_id: UUID
    status: str
    message: str


class PaginatedURLResponse(BaseModel):
    items: list[URLResponse]
    total: int
    page: int
    limit: int
    pages: int


class UserCreate(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class HealthResponse(BaseModel):
    status: str
    kafka: bool
    redis: bool
    db: bool
