# AI-Assisted Engineering Log

Use this log for substantial AI-assisted changes. The goal is not to count prompts; it is to preserve evidence of understanding and independent engineering judgment.

| Date | Task | AI suggestion | Human review/change | Tests/evidence | Learning |
|---|---|---|---|---|---|
| YYYY-MM-DD | Example: request permissions | Proposed generic object permission | Replaced with role-aware queryset isolation and API tests | `test_collection_api.py` | Frontend visibility is not authorization |

## Rules

- do not merge code you cannot explain;
- verify library behavior in official documentation;
- add or revise tests for generated logic;
- document security-sensitive decisions;
- keep commits focused and reviewable;
- never claim AI-generated work was independently written without assistance.
