# SAP ABAP Development Workspace

This workspace is configured for AI-assisted SAP ABAP development through the **abap-mcp** MCP server, which connects directly to an SAP ABAP system via ADT (ABAP Development Tools) services. These instructions apply to every chat request in this workspace.

## MCP Server: abap-mcp

The server is configured in `.vscode/mcp.json` (VS Code / GitHub Copilot). It exposes the following tools:

| Tool | Purpose | Safety |
|------|---------|--------|
| `GetObjectInfo` | Retrieve source code / definition of any ABAP object (18 object types) | Read-only |
| `SearchObject` | Find ABAP objects by name or pattern | Read-only |
| `WhereUsedSearch` | Dependency / usage analysis for an object | Read-only |
| `data_preview` | Execute SELECT-only queries on tables and CDS views | Read-only |
| `sap_help_search` / `sap_help_get` | Search and retrieve official SAP Help Portal documentation | Read-only |
| `sap_community_search` | Search SAP Community blogs and Q&A | Read-only |
| `CreateAIObject` | Create new ABAP objects | Write — **$TMP package only** |
| `ChangeAIObject` | Modify existing ABAP objects | Write — **$TMP objects only** |
| `ActivateObject` | Activate an object and run syntax check | Write — **Z*/Y* objects only** |

## Available Agents (`.github/agents/`)

Start with **ABAP-Architect** — it is the single user-invocable entry point that classifies the request and delegates to the right specialist:

- **ABAP-Architect** — top-level orchestrator; delegates to all specialists below
- **RAP-Analysis** — plans end-to-end RAP applications; orchestrates the six `task-*` agents
- **SAP-Research** — clean core compliance and cloud-readiness research
- **ABAP-Modernization** — legacy code analysis and modernization planning
- **ABAP-Unit** — ABAP Unit test classes with test doubles (AAA pattern)
- **amdp** — AMDP / SQLScript / HANA pushdown engineering
- **task-cds-creation** — CDS view entities (interface / consumption / projection layers)
- **task-bdef-creation** — behavior definitions (managed/unmanaged, draft, validations, actions)
- **task-behavior-impl** — behavior pool classes with EML (handler/saver)
- **task-dcl-security** — DCL row-level access control
- **task-metadata-extension** — Fiori UI annotations (DDLX)
- **task-service-definition** — OData service exposure (SRVD)

The `task-*` agents and specialists are subagents (`user-invocable: false`); invoke them through ABAP-Architect or RAP-Analysis.

## Available Skills (`.github/skills/`)

Skills auto-load based on the request — see [.github/skills/README.md](.github/skills/README.md) for the full index: get-object-info, search-object, where-used-search, create-ai-object, change-ai-object, activate-object, data-preview, sap-help-search, sap-community-search.

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

- `.vscode/mcp.json` contains SAP credentials — never commit it; keep it in `.gitignore`.
- Never echo SAP passwords, hostnames, or proxy credentials into chat output, generated code, or documentation.
