# Agent Copy Design

## Context

Agent management already supports creating and editing Agents, tracking latest and active versions separately, and activating a specific version from the history dialog. Users now need a way to reuse an existing Agent as the starting point for a new Agent.

The copy action should use the source Agent's current effective configuration, because that is the version known to be usable by active scenarios. The copied Agent must still go through the existing create flow so the user can choose a new unique name and adjust details before saving.

## Goals

- Add an Agent copy entry from the Agent card.
- Copy the source Agent's current active configuration into the existing create wizard.
- Require the user to enter a new Agent name before saving.
- Create the copied Agent through the existing `createAgent` flow.
- Keep the copied Agent as a new draft with its own `v1` version.

## Non-Goals

- Do not add one-click backend duplication with generated names.
- Do not add per-version copy actions in the history dialog.
- Do not automatically activate the copied Agent.
- Do not change the existing version activation model.

## User Flow

1. User opens Agent Management.
2. User clicks `更多` on an Agent card.
3. User chooses `复制`.
4. The existing Agent wizard opens in create mode with title `复制 Agent`.
5. The form is prefilled from the source Agent's active configuration.
6. The `agent_name` field is empty and must pass the existing name validation.
7. User edits fields as needed and saves.
8. Frontend calls the existing create API.
9. The new Agent appears as a draft with version `v1`.

## Data Source

The copy form uses active fields first:

- `content`: `active_content`, fallback to `content`.
- `tags`: `active_tags`, fallback to `tags`.
- `type`: source Agent `type`.
- `role`, `goal`, `backstory`, and `skills`: parsed from the selected content.

The copied form must not keep the source `id`, `agent_name`, `version`, `active_version`, or status. Those belong to the original Agent.

## UI Behavior

The `更多` menu in each Agent card gets a `复制` item. Copy is allowed for read-only Agents because it creates a new Agent owned by the current user instead of modifying the original. The create wizard title changes to `复制 Agent` only for this flow.

The type selector stays disabled because the copied configuration is tied to the source Agent type. Other editable fields remain adjustable: role, goal, backstory, skills, and category tag.

If the source Agent has no usable content after applying the active-content fallback, the UI shows `当前 Agent 没有可复制的生效配置` and does not open the wizard.

## Backend Behavior

No new backend endpoint is required for the first version. The frontend submits the copied Agent through `POST /agents` using the existing `AgentCreate` payload:

- `agent_name`: user-entered new name.
- `type`: copied source type.
- `content`: YAML generated from the copied and edited form.
- `tags`: copied or edited category tag.

The existing backend create path creates a new Agent in `draft` status with initial version `v1`.

## Error Handling

- Name conflicts use the existing name-check and create conflict handling.
- Category validation uses the existing create validation.
- YAML parsing should use the existing parser behavior. Fields that cannot be parsed remain blank, while the raw copied content still drives the preview after the user edits.
- API failures use the existing message handling around Agent creation.

## Test Plan

- Add a UI contract test that verifies the Agent card menu includes `复制`.
- Verify copy opens create mode rather than edit mode.
- Verify the copied form clears `agent_name` and `id`.
- Verify active fields are preferred: `active_content` and `active_tags`.
- Verify save still calls `createAgent`, not `updateAgent`.
- Verify the card-level direct `activate(row)` action remains absent.

## Open Decisions

None. The first version copies the current active configuration from the card menu into the existing create wizard.
