from pydantic import BaseModel


class LivenessResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, bool]


class AppHealthResponse(BaseModel):
    service: str
    version: str
    environment: str
    uptime_seconds: float
    status: str
