from typing import Literal

from pydantic import BaseModel


class WorkflowSummary(BaseModel):
    id: str
    name: str
    description: str
    trigger: str
    status: Literal["active", "inactive"]
    tools: list[str]
