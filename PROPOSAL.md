# Intelligence Platform — Proposal

## Summary
Full-stack Python + React developer with 20+ years building reporting-focused systems. I deliver end-to-end implementation without heavy supervision.

## Relevant Experience

**Business Intelligence Platform** — Built CRM with complex reporting (deals pipeline, activity streams, company hierarchies)

**Healthcare Intelligence** — FastAPI + PostgreSQL system with multi-source data aggregation

**Code reference:** https://github.com/9KMan/reporting-api-poc

This POC demonstrates my approach to the exact fallback pattern you're describing.

---

## Answer: Reporting API with Fallback Logic

I use a layered service pattern — query builder → executor → result transformer. Fallback chain is explicit at the application layer, not buried in SQL.

```python
class ReportFallbackService:
    async def get_with_fallback(self, filters):
        for source in [PRIMARY, SECONDARY, FALLBACK]:
            results = await self.query_source(source, filters)
            if results:
                return {"data": results, "source": source}
        return {"data": [], "source": "exhausted"}
```

**Why this works:**
- Clear: fallback chain is readable code
- Testable: mock each source independently
- Maintainable: add new sources without rewriting queries

Full implementation: See `backend/main.py` in the repo.

---

## Answer: API vs Frontend Responsibilities

**API does:**
- Filtering, pagination, sorting (database-level)
- Returns `total_count` for pagination

**Frontend does:**
- Debounced search (300-500ms delay)
- TanStack Query caching (30s stale time)
- Loading skeletons

Full explanation: See `SCREENING_ANSWERS.md` in the repo.

---

## Rate & Availability

**Hourly: $85-95/hr** (flexible based on scope)

- 25-30 hrs/week available
- GMT+7 timezone (within your ±2hr window)
- Can start within 48 hours

---

## Approach

1. You define architecture and approach
2. I take ownership of implementation slices
3. Small, clear tasks with working deliverables
4. Direct communication, minimal meetings

---

**Ready to discuss your architecture and deliver these reporting endpoints.**

— Boos