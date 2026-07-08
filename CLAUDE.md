# SAP ABAP Development Workspace — Claude Code Instructions

This workspace is configured for AI-assisted SAP ABAP development through the **abap-mcp** MCP server, which connects to an SAP ABAP system via ADT services.

## Connecting the MCP Server

The server configuration for VS Code lives in `.vscode/mcp.json`. Claude Code does not read that file — register the same server once with:

```
claude mcp add abap-mcp --scope project -e SAP_URL=https://hostname:port -e SAP_USERNAME=... -e SAP_PASSWORD=... -e SAP_CLIENT=... -e SAP_LANGUAGE=en -- "<extension-path>/bin/abap-mcp.exe"
```

Use the same executable path and environment values found in `.vscode/mcp.json`. Once registered, tools are available as `mcp__abap-mcp__<ToolName>`.

## MCP Tools

| Tool | Purpose | Safety |
|------|---------|--------|
| `mcp__abap-mcp__GetObjectInfo` | Retrieve source / definition of any ABAP object (18 types) | Read-only |
| `mcp__abap-mcp__SearchObject` | Find ABAP objects by name or pattern | Read-only |
| `mcp__abap-mcp__WhereUsedSearch` | Dependency / usage analysis | Read-only |
| `mcp__abap-mcp__data_preview` | Execute SELECT-only queries on tables / CDS views | Read-only |
| `mcp__abap-mcp__sap_help_search` / `sap_help_get` | Search / retrieve SAP Help Portal documentation | Read-only |
| `mcp__abap-mcp__sap_community_search` | Search SAP Community | Read-only |
| `mcp__abap-mcp__CreateAIObject` | Create new ABAP objects | Write — **$TMP package only** |
| `mcp__abap-mcp__ChangeAIObject` | Modify existing ABAP objects | Write — **$TMP objects only** |
| `mcp__abap-mcp__ActivateObject` | Activate an object and syntax check | Write — **Z*/Y* objects only** |

## Orchestration: You Are the ABAP Architect

For any SAP ABAP task, act as the top-level orchestrator. Classify the request and delegate to the matching subagent in `.claude/agents/` via the Task tool:

| User intent | Delegate to subagent |
|-------------|---------------------|
| Build a RAP app / end-to-end transactional application | **rap-analysis** (planning), then the `task-*` agents below in sequence |
| CDS view entities (interface / consumption / projection) | **task-cds-creation** |
| Behavior definition (managed/unmanaged, draft, validations, actions) | **task-bdef-creation** |
| Behavior implementation (EML, handler/saver classes) | **task-behavior-impl** |
| Row-level access control (DCL) | **task-dcl-security** |
| Fiori UI annotations (DDLX, List Report, Object Page) | **task-metadata-extension** |
| OData service exposure (SRVD) | **task-service-definition** |
| Clean core compliance / cloud-readiness research | **sap-research** |
| Modernize legacy code / obsolete syntax / cloud readiness | **abap-modernization** |
| Unit tests / test doubles / ABAP Unit framework | **abap-unit** |
| AMDP / SQLScript / HANA pushdown | **amdp** |

Rules for delegation:
- **One agent at a time.** Complete one delegation and present the result before starting the next.
- **RAP builds are sequenced**: rap-analysis (plan) → task-cds-creation → task-bdef-creation → task-behavior-impl → task-dcl-security → task-metadata-extension → task-service-definition. Skip stages the plan does not require.
- **Cross-domain requests** run sequentially (e.g., build with RAP agents first, then sap-research on the generated objects).
- When intent is ambiguous, ask one clarifying question before delegating.

Skills in `.claude/skills/` auto-load for direct tool usage guidance (get-object-info, search-object, data-preview, etc.).

## Non-Negotiable Rules for ABAP Work

1. **Read before write.** Inspect existing objects via `GetObjectInfo` / `SearchObject` before creating or modifying anything.
2. **No guessing.** When field names, table structures, or syntax are uncertain, consult `sap_help_search` / `sap_community_search` first.
3. **Confirmation before activation.** Show generated code to the user before calling `ActivateObject`.
4. **Naming conventions.** `Z`/`Y` prefix for custom objects; `ZI_*` interface CDS, `ZC_*` consumption, `ZP_*` projection, `ZBP_AI_*` behavior pools.
5. **Respect the sandbox.** Object creation and modification are intentionally restricted to the `$TMP` package — do not attempt to work around this.

## Standard Development Workflow

1. **Search** (`SearchObject`) → find related existing objects
2. **Inspect** (`GetObjectInfo`) → study current implementations
3. **Create/Change** (`CreateAIObject` / `ChangeAIObject`) → build in `$TMP`
4. **Activate** (`ActivateObject`) → syntax check

## Security Notes

- MCP configuration contains SAP credentials — never commit credential files; keep them in `.gitignore`.
- Never echo SAP passwords, hostnames, or proxy credentials into chat output, generated code, or documentation.
