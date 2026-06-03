# Public Scenario Runtime APIs

这两个接口供意图识别和运行时获取场景配置使用，均无需鉴权。公网入口为 `http://43.135.134.42/public/...`，服务内部路径同样为 `/public/...`。接口只返回已激活场景，并且详情中的 Agent 配置来自 Agent 的已激活版本字段 `active_content`，没有已激活版本内容时回退到 `content`。

## POST /public/scenarios

获取所有可用场景的名称和描述。

### Request

```json
{}
```

### Response 200

```json
{
  "scenarios": [
    {
      "name": "alert_analysis",
      "description": "告警根因分析多智能体",
      "sub_type_hint": "",
      "keyword_hint": ""
    }
  ],
  "total": 1
}
```

### 字段说明

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `scenarios[].name` | `str` | 场景名称 |
| `scenarios[].description` | `str` | 场景描述 |
| `scenarios[].sub_type_hint` | `str` | 子类型提示，辅助意图识别区分相似场景 |
| `scenarios[].keyword_hint` | `str` | 关键词提示 |
| `total` | `int` | 返回数量 |

## POST /public/scenarios/detail

获取指定场景完整配置，包含 Planner Agent 和所有启用的 Expert Agent 配置。不返回 routing_rules。

### Request

```json
{
  "name": "alert_analysis"
}
```

### Response 200

```json
{
  "name": "alert_analysis",
  "description": "告警根因分析多智能体",
  "sub_type_hint": "",
  "keyword_hint": "",
  "skill_selector_dims": [],
  "planner": {
    "name": "alert_planner",
    "role": "...",
    "goal": "...",
    "backstory": "...",
    "skills": ["alert_sop_guide"]
  },
  "experts": [
    {
      "name": "es_expert_agent",
      "role": "...",
      "goal": "...",
      "backstory": "",
      "skills": ["es_cluster_check"]
    }
  ]
}
```

### Agent YAML 标准格式

标准字段统一使用 `backstory`，不再使用 `backstory_extra`。历史数据中如存在 `backstory_extra`，服务端读取时会兼容解析为 `backstory`。

```yaml
name: alert_planner
role: 规划专家
goal: |
  协调专家团队进行系统性分析，委派相应专家并汇总结论，输出完整报告。
backstory: |
  补充约束规则、领域背景或输出要求。
skills:
  - alert_sop_guide
```

校验规则：

- 顶层必须是 YAML 对象。
- `name` 可选；如果填写，必须等于 Agent 名称。
- `role` 必须是非空字符串。
- `goal` 必须是非空字符串。
- `backstory` 可选；填写时必须是字符串。
- `skills` 必须是字符串数组，可为空数组。

### 字段说明

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `name` | `str` | 场景名称 |
| `description` | `str` | 场景描述 |
| `sub_type_hint` | `str` | 子类型提示 |
| `keyword_hint` | `str` | 关键词提示 |
| `skill_selector_dims` | `list[str]` | Skill 选择维度 |
| `planner.name` | `str` | Planner Agent 名称 |
| `planner.role` | `str` | Planner 角色定义 |
| `planner.goal` | `str` | Planner 目标描述 |
| `planner.backstory` | `str` | Planner 背景补充 |
| `planner.skills` | `list[str]` | Planner 挂载的 Skill 名称列表 |
| `experts[].name` | `str` | Expert Agent 名称 |
| `experts[].role` | `str` | Expert 角色定义 |
| `experts[].goal` | `str` | Expert 目标描述 |
| `experts[].backstory` | `str` | Expert 背景补充 |
| `experts[].skills` | `list[str]` | Expert 挂载的 Skill 名称列表 |

### 错误响应

| HTTP 状态 | detail | 说明 |
| --- | --- | --- |
| `404` | `Scenario not found` | 场景不存在或未激活 |
| `400` | `Scenario planner is required` | 场景没有配置 Planner |
| `400` | `Scenario agents are not active: name1, name2` | 关联 Agent 不存在或未激活 |
| `400` | `智能体配置校验失败：agent_name；配置内容无法解析，请检查格式` | Agent 没有可用配置、YAML 无法解析、顶层不是对象，或字段类型不符合标准 |

## curl 示例

```bash
curl -fsS -X POST http://43.135.134.42/public/scenarios -H 'Content-Type: application/json' -d '{}'
curl -fsS -X POST http://43.135.134.42/public/scenarios/detail -H 'Content-Type: application/json' -d '{"name":"alert_analysis"}'
```
