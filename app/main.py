from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import HTMLResponse
from pymysql.err import IntegrityError

from app.core.db import init_schema
from app.core.security import CurrentUser, get_current_user
from app.schemas import (
    AgentCreate,
    AgentUpdate,
    ExecutionLogPage,
    NameCheckIn,
    NameCheckOut,
    PanoramaAgentSlotCreate,
    PanoramaAgentSlotUpdate,
    PanoramaLayerCreate,
    PanoramaLayerUpdate,
    PanoramaNodeCreate,
    PanoramaNodeTagAssign,
    PanoramaNodeUpdate,
    PanoramaScenarioSlotCreate,
    PanoramaScenarioSlotUpdate,
    PanoramaTagCreate,
    PanoramaTagUpdate,
    PublicScenarioDetailIn,
    PublicScenarioDetailOut,
    PublicScenarioListIn,
    PublicScenarioListOut,
    RollbackIn,
    ScenarioCreate,
    ScenarioUpdate,
)
from app.services import panorama_store
from app.services import store
from app.services.permissions import OwnershipError


app = FastAPI(title="Agent Management Service", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_schema()


@app.exception_handler(OwnershipError)
async def ownership_error_handler(_, exc: OwnershipError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


def _duplicate_error(exc: IntegrityError):
    raise HTTPException(status_code=409, detail="Name already exists") from exc


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent-mgmt-service"}


@app.get("/panorama/tree")
def panorama_tree(user: CurrentUser = Depends(get_current_user)):
    return {"tree": panorama_store.get_tree()}


@app.get("/panorama/stats")
def panorama_stats(user: CurrentUser = Depends(get_current_user)):
    return panorama_store.get_stats()


@app.get("/panorama/layers")
def panorama_layers(user: CurrentUser = Depends(get_current_user)):
    return panorama_store.list_layers()


@app.post("/panorama/layers", status_code=201)
def create_panorama_layer(req: PanoramaLayerCreate, user: CurrentUser = Depends(get_current_user)):
    return panorama_store.create_layer(req)


@app.put("/panorama/layers/{layer_id}")
def update_panorama_layer(layer_id: int, req: PanoramaLayerUpdate, user: CurrentUser = Depends(get_current_user)):
    row = panorama_store.update_layer(layer_id, req)
    if not row:
        raise HTTPException(status_code=404, detail="层级不存在")
    return row


@app.delete("/panorama/layers/{layer_id}")
def delete_panorama_layer(layer_id: int, user: CurrentUser = Depends(get_current_user)):
    if not panorama_store.delete_layer(layer_id):
        raise HTTPException(status_code=404, detail="层级不存在")
    return {"ok": True}


@app.get("/panorama/nodes")
def panorama_nodes(user: CurrentUser = Depends(get_current_user)):
    return panorama_store.list_nodes()


@app.post("/panorama/nodes", status_code=201)
def create_panorama_node(req: PanoramaNodeCreate, user: CurrentUser = Depends(get_current_user)):
    return panorama_store.create_node(req)


@app.put("/panorama/nodes/{node_id}")
def update_panorama_node(node_id: int, req: PanoramaNodeUpdate, user: CurrentUser = Depends(get_current_user)):
    row = panorama_store.update_node(node_id, req)
    if not row:
        raise HTTPException(status_code=404, detail="节点不存在")
    return row


@app.delete("/panorama/nodes/{node_id}")
def delete_panorama_node(node_id: int, user: CurrentUser = Depends(get_current_user)):
    if not panorama_store.delete_node(node_id):
        raise HTTPException(status_code=404, detail="节点不存在")
    return {"ok": True}


@app.post("/panorama/nodes/{node_id}/tags")
def assign_panorama_node_tag(node_id: int, req: PanoramaNodeTagAssign, user: CurrentUser = Depends(get_current_user)):
    panorama_store.assign_node_tag(node_id, req.tag_id)
    return {"ok": True}


@app.delete("/panorama/nodes/{node_id}/tags/{tag_id}")
def remove_panorama_node_tag(node_id: int, tag_id: int, user: CurrentUser = Depends(get_current_user)):
    if not panorama_store.remove_node_tag(node_id, tag_id):
        raise HTTPException(status_code=404, detail="标签关联不存在")
    return {"ok": True}


@app.get("/panorama/tags")
def panorama_tags(user: CurrentUser = Depends(get_current_user)):
    return panorama_store.list_tags()


@app.post("/panorama/tags", status_code=201)
def create_panorama_tag(req: PanoramaTagCreate, user: CurrentUser = Depends(get_current_user)):
    return panorama_store.create_tag(req)


@app.put("/panorama/tags/{tag_id}")
def update_panorama_tag(tag_id: int, req: PanoramaTagUpdate, user: CurrentUser = Depends(get_current_user)):
    row = panorama_store.update_tag(tag_id, req)
    if not row:
        raise HTTPException(status_code=404, detail="标签不存在")
    return row


@app.delete("/panorama/tags/{tag_id}")
def delete_panorama_tag(tag_id: int, user: CurrentUser = Depends(get_current_user)):
    if not panorama_store.delete_tag(tag_id):
        raise HTTPException(status_code=404, detail="标签不存在")
    return {"ok": True}


@app.get("/panorama/nodes/{node_id}/slots")
def panorama_node_slots(node_id: int, user: CurrentUser = Depends(get_current_user)):
    return panorama_store.list_node_slots(node_id)


@app.post("/panorama/nodes/{node_id}/agent-slots", status_code=201)
def create_panorama_agent_slot(node_id: int, req: PanoramaAgentSlotCreate, user: CurrentUser = Depends(get_current_user)):
    return panorama_store.create_agent_slot(node_id, req)


@app.put("/panorama/agent-slots/{slot_id}")
def update_panorama_agent_slot(slot_id: int, req: PanoramaAgentSlotUpdate, user: CurrentUser = Depends(get_current_user)):
    row = panorama_store.update_agent_slot(slot_id, req)
    if not row:
        raise HTTPException(status_code=404, detail="槽位不存在")
    return row


@app.delete("/panorama/agent-slots/{slot_id}")
def delete_panorama_agent_slot(slot_id: int, user: CurrentUser = Depends(get_current_user)):
    if not panorama_store.delete_agent_slot(slot_id):
        raise HTTPException(status_code=404, detail="槽位不存在")
    return {"ok": True}


@app.post("/panorama/nodes/{node_id}/scenario-slots", status_code=201)
def create_panorama_scenario_slot(node_id: int, req: PanoramaScenarioSlotCreate, user: CurrentUser = Depends(get_current_user)):
    return panorama_store.create_scenario_slot(node_id, req)


@app.put("/panorama/scenario-slots/{slot_id}")
def update_panorama_scenario_slot(slot_id: int, req: PanoramaScenarioSlotUpdate, user: CurrentUser = Depends(get_current_user)):
    row = panorama_store.update_scenario_slot(slot_id, req)
    if not row:
        raise HTTPException(status_code=404, detail="槽位不存在")
    return row


@app.delete("/panorama/scenario-slots/{slot_id}")
def delete_panorama_scenario_slot(slot_id: int, user: CurrentUser = Depends(get_current_user)):
    if not panorama_store.delete_scenario_slot(slot_id):
        raise HTTPException(status_code=404, detail="槽位不存在")
    return {"ok": True}


@app.post("/agents/check-name", response_model=NameCheckOut)
def check_agent_name(body: NameCheckIn):
    available = store.check_name(store.AGENT_TABLE, "agent_name", body.name)
    return {"available": available, "message": "名称可用" if available else "名称已存在"}


@app.get("/agents")
def list_agents(
    scope: str = Query("mine", pattern="^(mine|all)$"),
    status: str = None,
    type: str = Query(None),
    category_codes: str = Query(None),
    user: CurrentUser = Depends(get_current_user),
):
    return store.list_agents(user, scope, status, type, category_codes)


@app.get("/agent-categories")
def list_agent_categories(user: CurrentUser = Depends(get_current_user)):
    return store.list_agent_categories()


@app.post("/agents", status_code=201)
def create_agent(req: AgentCreate, user: CurrentUser = Depends(get_current_user)):
    try:
        return store.create_agent(req, user)
    except IntegrityError as exc:
        _duplicate_error(exc)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/agents/{agent_id}")
def get_agent(agent_id: int, user: CurrentUser = Depends(get_current_user)):
    row = store.get_agent(agent_id, user)
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    return row


@app.put("/agents/{agent_id}")
def update_agent(agent_id: int, req: AgentUpdate, user: CurrentUser = Depends(get_current_user)):
    try:
        row = store.update_agent(agent_id, req, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    return row


@app.delete("/agents/{agent_id}")
def delete_agent(agent_id: int, user: CurrentUser = Depends(get_current_user)):
    result = store.delete_agent(agent_id, user)
    if result is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    if result is False:
        raise HTTPException(status_code=400, detail="Active agent cannot be deleted")
    return {"message": "删除成功"}


@app.post("/agents/{agent_id}/activate")
def activate_agent(agent_id: int, user: CurrentUser = Depends(get_current_user)):
    try:
        row, _ = store.set_agent_status(agent_id, "active", user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    return row


@app.post("/agents/{agent_id}/deactivate")
def deactivate_agent(agent_id: int, user: CurrentUser = Depends(get_current_user)):
    row, blocked = store.set_agent_status(agent_id, "inactive", user)
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found")
    if blocked:
        raise HTTPException(status_code=400, detail=f"Agent is used by active scenarios: {', '.join(blocked)}")
    return row


@app.get("/agents/{agent_id}/versions")
def list_agent_versions(agent_id: int, user: CurrentUser = Depends(get_current_user)):
    return store.list_agent_versions(agent_id)


@app.post("/agents/{agent_id}/versions/{version_id}/activate")
def activate_agent_version(agent_id: int, version_id: int, user: CurrentUser = Depends(get_current_user)):
    try:
        result = store.activate_agent_version(agent_id, version_id, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="Agent or version not found")
    return result


@app.get("/agents/{agent_id}/related-scenarios")
def list_agent_related_scenarios(agent_id: int, user: CurrentUser = Depends(get_current_user)):
    rows = store.list_agent_related_scenarios(agent_id, user)
    if rows is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return rows


@app.post("/agents/{agent_id}/rollback")
def rollback_agent(agent_id: int, req: RollbackIn, user: CurrentUser = Depends(get_current_user)):
    try:
        row = store.rollback_agent(agent_id, req.version_id, user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not row:
        raise HTTPException(status_code=404, detail="Agent or version not found")
    return row


@app.post("/scenarios/check-name", response_model=NameCheckOut)
def check_scenario_name(body: NameCheckIn):
    available = store.check_name(store.SCENARIO_TABLE, "scenario_name", body.name)
    return {"available": available, "message": "名称可用" if available else "名称已存在"}


@app.post("/public/scenarios", response_model=PublicScenarioListOut)
def list_public_scenarios(_: PublicScenarioListIn):
    return store.list_public_scenarios()


@app.post("/public/scenarios/detail", response_model=PublicScenarioDetailOut)
def get_public_scenario_detail(req: PublicScenarioDetailIn):
    try:
        detail = store.get_public_scenario_detail(req.name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not detail:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return detail


@app.get("/scenarios")
def list_scenarios(
    scope: str = Query("mine", pattern="^(mine|all)$"),
    status: str = None,
    user: CurrentUser = Depends(get_current_user),
):
    return store.list_scenarios(user, scope, status)


@app.post("/scenarios", status_code=201)
def create_scenario(req: ScenarioCreate, user: CurrentUser = Depends(get_current_user)):
    try:
        return store.create_scenario(req, user)
    except IntegrityError as exc:
        _duplicate_error(exc)


@app.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: int, user: CurrentUser = Depends(get_current_user)):
    row = store.get_scenario(scenario_id, user)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return row


@app.put("/scenarios/{scenario_id}")
def update_scenario(scenario_id: int, req: ScenarioUpdate, user: CurrentUser = Depends(get_current_user)):
    row = store.update_scenario(scenario_id, req, user)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return row


@app.delete("/scenarios/{scenario_id}")
def delete_scenario(scenario_id: int, user: CurrentUser = Depends(get_current_user)):
    result = store.delete_scenario(scenario_id, user)
    if result is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if result is False:
        raise HTTPException(status_code=400, detail="Active scenario cannot be deleted")
    return {"message": "删除成功"}


@app.post("/scenarios/{scenario_id}/activate")
def activate_scenario(scenario_id: int, user: CurrentUser = Depends(get_current_user)):
    row, not_ready = store.set_scenario_status(scenario_id, "active", user)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if not_ready:
        raise HTTPException(status_code=400, detail=f"Agents are not active: {', '.join(not_ready)}")
    return row


@app.post("/scenarios/{scenario_id}/deactivate")
def deactivate_scenario(scenario_id: int, user: CurrentUser = Depends(get_current_user)):
    row, _ = store.set_scenario_status(scenario_id, "inactive", user)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return row


@app.get("/scenarios/{scenario_id}/versions")
def list_scenario_versions(scenario_id: int, user: CurrentUser = Depends(get_current_user)):
    return store.list_scenario_versions(scenario_id)


@app.post("/scenarios/{scenario_id}/rollback")
def rollback_scenario(scenario_id: int, req: RollbackIn, user: CurrentUser = Depends(get_current_user)):
    row = store.rollback_scenario(scenario_id, req.version_id, user)
    if not row:
        raise HTTPException(status_code=404, detail="Scenario or version not found")
    return row


@app.get("/logs", response_model=ExecutionLogPage)
def list_logs(
    scenario_name: str = None,
    system_id: str = None,
    alert_key: str = None,
    alert_source: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return store.list_logs(scenario_name, system_id, alert_key, alert_source, page, page_size)


@app.get("/logs/by-alert-key", response_model=ExecutionLogPage)
def list_logs_by_alert_key(
    alert_key: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return store.list_logs_by_alert_key(alert_key, page, page_size)


@app.get("/logs/stats")
def log_stats(scenario_name: str = None):
    return store.log_stats(scenario_name)


@app.get("/llm-stats/summary")
def llm_stats_summary(days: int = Query(7, ge=1, le=90)):
    return store.llm_stats_summary(days)


@app.get("/llm-stats/failures", response_model=ExecutionLogPage)
def llm_stats_failures(
    days: int = Query(7, ge=1, le=90),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scenario_name: str = None,
    error_type: str = None,
    keyword: str = None,
):
    return store.llm_stats_failures(days, page, page_size, scenario_name, error_type, keyword)


@app.get("/llm-stats/by-run/{run_id}")
def llm_stats_by_run(run_id: str):
    row = store.llm_stats_by_run(run_id)
    if not row:
        raise HTTPException(status_code=404, detail="LLM run not found")
    return row


@app.get("/llm-stats/by-scenario")
def llm_stats_by_scenario(
    days: int = Query(7, ge=1, le=90),
    only_failures: bool = False,
    scenario_name: str = None,
    keyword: str = None,
    run_id: str = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return store.llm_stats_by_scenario(days, only_failures, scenario_name, keyword, run_id, page, page_size)


@app.get("/logs/by-run/{run_id}/html", response_class=HTMLResponse)
def get_log_html_by_run(run_id: str):
    row = store.get_log_html_by_run(run_id)
    if not row or not row.get("html_content"):
        raise HTTPException(status_code=404, detail="HTML report not found")
    return HTMLResponse(content=row["html_content"])


@app.get("/logs/{log_id}/html", response_class=HTMLResponse)
def get_log_html(log_id: int):
    row = store.get_log_html(log_id)
    if not row or not row.get("html_content"):
        raise HTTPException(status_code=404, detail="HTML report not found")
    return HTMLResponse(content=row["html_content"])


@app.get("/public/log-viewer", response_class=HTMLResponse)
def public_log_viewer(run_id: str = Query(..., min_length=1)):
    row = store.get_log_html_by_run(run_id)
    if not row or not row.get("html_content"):
        raise HTTPException(status_code=404, detail="Log not found")
    return HTMLResponse(content=row["html_content"])
