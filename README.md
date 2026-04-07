# Intelligence Platform - Reporting API POC

Full Stack Developer position submission. Built this POC to demonstrate competence in handling non-trivial business logic, not just CRUD.

## What This POC Demonstrates

- **Primary → Secondary Fallback Logic** — clean, testable, maintainable
- **API + Frontend Integration** — filtering, pagination, source tracking
- **FastAPI + PostgreSQL** — proven stack
- **React + Jotai** — state management, query caching

## Project Structure

```
reporting-api-poc/
├── SPEC.md                 # Specification
├── SCREENING_ANSWERS.md     # Answers to screening questions with code
├── backend/
│   ├── main.py            # FastAPI with fallback service
│   ├── schema.sql         # PostgreSQL schema
│   └── requirements.txt  # Python dependencies
└── frontend/
    └── Dashboard.tsx      # React dashboard with filters + pagination
```

## Key Code

### Fallback Logic (main.py)

```python
class ReportFallbackService:
    async def get_with_fallback(self, filters, page, limit):
        for source_type in self.fallback_chain:
            results = await self.query_source(source_type, filters)
            if results:
                return {"data": results, "source": source_type}
        return {"data": [], "source": "exhausted"}
```

### API + Frontend Separation

- **API**: Filtering, pagination, sorting at database level
- **Frontend**: Debounced search, client-side caching (TanStack Query)

## To Run Locally

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Set DATABASE_URL, then: uvicorn main:app --reload

# Frontend
cd frontend
npm install
# Add to existing React project
```

## Screening Answers

See `SCREENING_ANSWERS.md` for detailed answers with working code.

---

**Rate expectation**: $80-100/hr for this role (based on skill level required)

**Timezone**: GMT+7 (within their ±2hr window)