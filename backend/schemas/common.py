from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: bool


class SuccessResponse(BaseModel):
    success: bool = True
    message: str
