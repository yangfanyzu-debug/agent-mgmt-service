from datetime import datetime
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, validator


NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


class NameCheckIn(BaseModel):
    name: str


class NameCheckOut(BaseModel):
    available: bool
    message: str


class AgentCreate(BaseModel):
    agent_name: str
    type: str
    content: str
    tags: str

    @validator("agent_name")
    def validate_name(cls, value):
        if not NAME_RE.match(value):
            raise ValueError("agent_name must start with a letter and contain only letters, digits, and underscores")
        return value

    @validator("type")
    def validate_type(cls, value):
        if value not in ("planner", "expert"):
            raise ValueError("type must be planner or expert")
        return value

    @validator("tags")
    def validate_tags(cls, value):
        if not value or not value.strip():
            raise ValueError("tags is required")
        return value.strip()


class AgentUpdate(BaseModel):
    content: str
    tags: Optional[str] = None

    @validator("tags")
    def validate_update_tags(cls, value):
        if value is not None and not value.strip():
            raise ValueError("tags cannot be empty")
        return value.strip() if value is not None else value


class RollbackIn(BaseModel):
    version_id: int


class ScenarioCreate(BaseModel):
    scenario_name: str
    description: Optional[str] = None
    sub_type_hint: Optional[str] = None
    keyword_hint: Optional[str] = None
    skill_selector_dims: Optional[List[str]] = None
    related_agents: Dict[str, Any]

    @validator("scenario_name")
    def validate_name(cls, value):
        if not NAME_RE.match(value):
            raise ValueError("scenario_name must start with a letter and contain only letters, digits, and underscores")
        return value


class ScenarioUpdate(BaseModel):
    description: Optional[str] = None
    sub_type_hint: Optional[str] = None
    keyword_hint: Optional[str] = None
    skill_selector_dims: Optional[List[str]] = None
    related_agents: Optional[Dict[str, Any]] = None


class PublicScenarioListIn(BaseModel):
    pass


class PublicScenarioSummary(BaseModel):
    name: str
    description: str
    sub_type_hint: str
    keyword_hint: str


class PublicScenarioListOut(BaseModel):
    scenarios: List[PublicScenarioSummary]
    total: int


class PublicScenarioDetailIn(BaseModel):
    name: str


class PublicAgentConfig(BaseModel):
    name: str
    role: str
    goal: str
    backstory: str
    skills: List[str]


class PublicScenarioDetailOut(BaseModel):
    name: str
    description: str
    sub_type_hint: str
    keyword_hint: str
    skill_selector_dims: List[str]
    planner: PublicAgentConfig
    experts: List[PublicAgentConfig]


class ExecutionLogPage(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[Dict[str, Any]]


class VersionItem(BaseModel):
    id: int
    version: str
    created_by_user_id: int
    created_by_username: str
    created_at: datetime
