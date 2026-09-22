from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["connected", "not_configured", "unavailable"]
