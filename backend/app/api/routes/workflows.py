from fastapi import APIRouter

from app.workflows.service import assistant_workflow
from app.workflows.models import WorkflowSummary

router = APIRouter()


@router.get("/workflows", response_model=list[WorkflowSummary])
async def list_workflows() -> list[WorkflowSummary]:
    return [assistant_workflow.summary]
