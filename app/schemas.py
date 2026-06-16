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


class PanoramaLayerCreate(BaseModel):
    name: str
    description: Optional[str] = None
    display_order: int = 0
    color: str = "#7F77DD"
    show_label: bool = True
    style_config: Optional[Dict[str, Any]] = None


class PanoramaLayerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    color: Optional[str] = None
    show_label: Optional[bool] = None
    style_config: Optional[Dict[str, Any]] = None


class PanoramaLayerOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    display_order: int
    color: str
    show_label: bool
    style_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class PanoramaNodeCreate(BaseModel):
    parent_id: Optional[int] = None
    layer_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    sort_order: int = 0
    data_binding_type: str = "none"

    @validator("data_binding_type")
    def validate_binding_type(cls, value):
        if value not in ("none", "scenario", "agent"):
            raise ValueError("data_binding_type must be none, scenario, or agent")
        return value


class PanoramaNodeUpdate(BaseModel):
    parent_id: Optional[int] = None
    layer_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    data_binding_type: Optional[str] = None

    @validator("data_binding_type")
    def validate_update_binding_type(cls, value):
        if value is not None and value not in ("none", "scenario", "agent"):
            raise ValueError("data_binding_type must be none, scenario, or agent")
        return value


class PanoramaNodeOut(BaseModel):
    id: int
    parent_id: Optional[int] = None
    layer_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    sort_order: int
    data_binding_type: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class PanoramaTagCreate(BaseModel):
    name: str
    description: Optional[str] = None
    border_color: str = "#F59E0B"


class PanoramaTagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    border_color: Optional[str] = None


class PanoramaTagOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    border_color: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class PanoramaNodeTagAssign(BaseModel):
    tag_id: int


class PanoramaAgentSlotCreate(BaseModel):
    display_name: str
    match_name: str
    description: Optional[str] = None
    sort_order: int = 0


class PanoramaAgentSlotUpdate(BaseModel):
    display_name: Optional[str] = None
    match_name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class PanoramaAgentSlotOut(BaseModel):
    id: int
    node_id: int
    display_name: str
    match_name: str
    description: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class PanoramaScenarioSlotCreate(BaseModel):
    display_name: str
    match_name: str
    description: Optional[str] = None
    sort_order: int = 0


class PanoramaScenarioSlotUpdate(BaseModel):
    display_name: Optional[str] = None
    match_name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class PanoramaScenarioSlotOut(BaseModel):
    id: int
    node_id: int
    display_name: str
    match_name: str
    description: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: Optional[datetime] = None
