# Reporting API POC — Intelligence Platform

## Context
Job application strategy: answer screening questions with concrete code, not just text.
Screening Q: "You have a reporting API with joins + fallback logic (primary → secondary). How would you structure it so it stays clear, testable, and maintainable?"

## Goal
Build the core reporting endpoint with join + fallback logic in FastAPI + PostgreSQL.
Minimal, focused, proves non-trivial business logic competence.

## Scope

### Backend (FastAPI + PostgreSQL)
- Data model: Reports with primary + fallback source logic
- One endpoint: `GET /reports/` with filtering + pagination
- Fallback pattern: primary_source → secondary_source (when primary returns nothing)
- Alembic migration for schema
- Unit tests for the fallback logic

### Frontend (React)
- Single dashboard: report list with filters + pagination
- Connects to the FastAPI endpoint
- Clean, production-like UI

### What's NOT included (MVP scope)
- Azure deployment
- Full RBAC (just the structure)
- Multiple report types
- Admin panel

## Technical Decisions

### Fallback Strategy
```python
# Layered query approach
result = await primary_query(filters)
if not result or result.exhausted:
    result = await secondary_query(filters)
return result
```

### Why this structure?
- Separates concerns: query builder vs executor vs serializer
- Testable: mock primary/secondary at each layer
- Maintainable: new sources added by implementing a new query layer
- Clear: fallback chain is explicit, not buried in WHERE clauses

### API Design
- `GET /reports/?page=1&limit=20&status=active`
- Returns: `{ data: [...], meta: { total, page, limit } }`
- Fallback metadata in response headers or response body

## Project Location
`/home/openclaw/projects/reporting-api-poc/`

## Status
[x] SPEC.md created
[x] FastAPI backend with fallback logic
[x] PostgreSQL schema + migration
[ ] Unit tests for fallback
[x] React frontend dashboard
[x] Screening answers written
[ ] GitHub push