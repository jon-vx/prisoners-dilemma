from pydantic import BaseModel


class StrategyResponse(BaseModel):
    key: str
    name: str
    description: str
