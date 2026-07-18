# Standard API error contracts (frozen v1).

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = "error"
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    """Standard error payload inside ApiEnvelope.errors."""

    errors: list[ErrorDetail] = Field(default_factory=list)

    @classmethod
    def from_message(cls, message: str, *, code: str = "error") -> ErrorResponse:
        return cls(errors=[ErrorDetail(code=code, message=message)])

    @classmethod
    def from_messages(cls, messages: list[str] | str) -> ErrorResponse:
        if isinstance(messages, str):
            messages = [messages]
        return cls(errors=[ErrorDetail(message=m) for m in messages])


class ApiError(Exception):
    """Raise from handlers; mapped to ErrorResponse by response helpers."""

    def __init__(
        self,
        message: str,
        *,
        status: int = 400,
        code: str = "error",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
