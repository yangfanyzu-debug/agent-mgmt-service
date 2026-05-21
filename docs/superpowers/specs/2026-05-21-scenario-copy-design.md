# Scenario Copy Design

## Context

Scenario management already supports creating, editing, activating, deactivating, deleting, viewing graph relationships, and listing historical versions. Users now need a way to reuse an existing scenario as a starting point for a new scenario.

The copy action should follow the Agent copy pattern: use the current scenario configuration, open the existing create wizard, clear the unique name, and let the user review or adjust details before saving.

## Goals

- Add a scenario copy entry from the scenario card menu.
- Copy the current scenario configuration into the existing create wizard.
- Require the user to enter a new scenario name before saving.
- Preserve the copied Planner and Expert selections for quick reuse.
- Create the copied scenario through the existing `createScenario` flow.

## Non-Goals

- Do not add one-click backend duplication with generated names.
- Do not add per-version copy actions in the history dialog.
- Do not automatically activate the copied scenario.
- Do not change scenario versioning, rollback, or activation behavior.

## User Flow

1. User opens Scenario Management.
2. User clicks `更多` on a scenario card.
3. User chooses `复制`.
4. The existing scenario wizard opens in create mode with title `复制场景`.
5. The form is prefilled from the source scenario's current configuration.
6. The `scenario_name` field is empty and must pass the existing name validation.
7. User edits description, Planner, or Expert selections as needed.
8. Frontend calls the existing create API.
9. The new scenario appears as a draft with version `v1`.

## Data Source

The copy form uses the source scenario's current fields:

- `description`: copied from the source scenario.
- `planner`: parsed from `related_agents.planner`.
- `experts`: parsed from enabled items in `related_agents.experts`.
- `sub_type_hint`: copied from the source scenario.
- `keyword_hint`: copied from the source scenario.
- `skill_selector_dims`: parsed from the source scenario.

The copied form must not keep the source `id`, `scenario_name`, `version`, or `status`. Those belong to the original scenario.

## UI Behavior

The `更多` menu in each scenario card gets a `复制` item. Copy is allowed for read-only scenarios because it creates a new scenario owned by the current user instead of modifying the original. The create wizard title changes to `复制场景` only for this flow.

The copied form opens at step 1 of the existing wizard. Agent selections are visible and editable exactly like the normal create flow. The right-side preview updates from the copied form state.

If the source scenario's `related_agents` cannot be parsed into a usable object, the UI shows `当前场景配置无法复制` and does not open the wizard.

## Backend Behavior

No new backend endpoint is required for the first version. The frontend submits the copied scenario through `POST /scenarios` using the existing `ScenarioCreate` payload:

- `scenario_name`: user-entered new name.
- `description`: copied or edited description.
- `sub_type_hint`: copied source value.
- `keyword_hint`: copied source value.
- `skill_selector_dims`: copied source value.
- `related_agents`: copied or edited Planner and Expert selections.

The existing backend create path creates a new scenario in `draft` status with initial version `v1`.

## Error Handling

- Name conflicts use the existing name-check and create conflict handling.
- Missing scenario name, description, or Planner uses existing wizard validation.
- Inactive copied Agents keep the current warning behavior after save and before activation.
- API failures use the existing message handling around scenario creation.

## Test Plan

- Add a UI contract test that verifies the scenario card menu includes `复制`.
- Verify `handleMore` routes `copy` to `openCopy(row)`.
- Verify copy opens create mode rather than edit mode.
- Verify the copied form clears `scenario_name` and `id`.
- Verify Planner, Experts, description, and hidden scenario fields are copied.
- Verify save still calls `createScenario`, not `updateScenario`.

## Open Decisions

None. The first version copies the current scenario configuration from the card menu into the existing create wizard.
