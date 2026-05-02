from pydantic import BaseModel, Field


class ProcessPRRequest(BaseModel):
    owner: str
    repo: str
    pull_number: int = Field(gt=0)


class ProcessPRResponse(BaseModel):
    status: str
    updated_files: list[str]
    commit_sha: str | None = None
    message: str
