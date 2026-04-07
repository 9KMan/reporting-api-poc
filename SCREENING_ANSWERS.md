# Screening Answers — Intelligence Platform

## Submit your proposal

You have a reporting API with joins + fallback logic (primary → secondary). How would you structure it so it stays clear, testable, and maintainable over time?

---

## Answer (with working code)

I use a **layered service pattern** that separates concerns: query building → execution → result transformation. This keeps fallback logic explicit and testable, not buried in SQL WHERE clauses.

### Core Implementation

```python
class ReportFallbackService:
    """
    Primary → Secondary → Fallback chain.
    Each source is tried in order until data is found.
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.fallback_chain = [SourceType.PRIMARY, SourceType.SECONDARY, SourceType.FALLBACK]
    
    async def get_with_fallback(self, filters: ReportFilter, page=1, limit=20):
        for source_type in self.fallback_chain:
            # Apply source type to filters
            current_filters = filters.model_copy()
            current_filters.source_type = source_type
            
            # Build and execute query
            query, params = self.query_builder.build(current_filters, page, limit)
            results = await self.pool.fetch(query, *params)
            
            if results:  # Found data from this source
                return ReportListResponse(
                    data=results,
                    source_info={"served_from": source_type.value}
                )
        
        # All sources exhausted
        return ReportListResponse(data=[], source_info={"exhausted": True})
```

### Why This Structure Works

| Principle | How It's Achieved |
|-----------|----------------|
| **Clear** | Fallback chain is explicit: `for source in chain: try → if success: break`. No hidden logic |
| **Testable** | Mock `pool.fetch` → test each fallback level independently |
| **Maintainable** | Add new source by appending to `fallback_chain` |
| **Transparent** | Response includes `source_info` showing which source provided data |

### The Key Insight

SQL JOINs aren't the right tool for source fallback. Instead:
1. **Query per source** — not one query with COALESCE
2. **Handle at application layer** — not database layer
3. **Return source metadata** — so UI can show "Data from: Primary" vs "Data from: Secondary"

This makes debugging straightforward and the behavior predictable.

---

## Answer Q2

You built a report API. UI needs filtering, pagination, fast response. What belongs in API vs frontend, and why?

---

### Answer (with implementation)

Here’s the clean separation:

### API Responsibilities

| What | Why |
|------|-----|
| **Filtering** | Requires database indexes, WHERE clauses. Filter *at the database*, not in Python |
| **Pagination** | OFFSET/LIMIT at DB level. Returns `total_count` so frontend knows pages |
| **Sorting** | Database handles ORDER BY most efficiently |
| **Data shape** | Return exactly what UI needs — no extra fields |

### Frontend Responsibilities

| What | Why |
|------|-----|
| **Debounced search** | Don’t hit API on every keystroke. Wait 300-500ms |
| **Client-side caching** | TanStack Query (React Query) handles this — skip fetch if data fresh |
| **Loading states** | Show skeletons while fetching |
| **Page size limits** | Respect API limits, show "Load More" vs all-at-once |

### Implementation

```python
# FastAPI endpoint — filtering + pagination at DB level
@app.get("/reports/")
async def get_reports(
    status: Optional[str] = None,
    priority: Optional[int] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
):
    # Build WHERE clause in Python, execute in DB
    params, where = build_filters(status, priority, search)
    
    # Single query with COUNT + data
    query = f"""
        SELECT * FROM reports
        WHERE {where}
        ORDER BY published_at DESC
        LIMIT $N OFFSET $M
        
        -- Total count (same WHERE)
        SELECT COUNT(*) FROM reports WHERE {where}
    """
    
    data, total = await pool.fetch_all(query, *params)
    
    return {
        "data": data,
        "meta": {"total": total, "page": page, "limit": limit, "has_more": len(data) == limit}
    }
```

```tsx
// React — client-side optimization
const { data, isLoading } = useQuery({
  queryKey: ['reports', filters],
  queryFn: () => fetchReports(filters),
  staleTime: 30_000, // 30s cache
});

// Debounce search input
const [search, setSearch] = useState('');
useEffect(() => {
  const timer = setTimeout(() => setFilters(s => ({ ...s, search })), 500);
  return () => clearTimeout(timer);
}, [search]);
```

### The Trade-off

- **Too much filtering in frontend**: Every keystroke hits API, slow response
- **Too much filtering in backend**: Hard to test, less flexible UI
- **Sweet spot**: Filtering/pagination at API, debouncing + caching at frontend

---

## Summary

I believe in **explicit over implicit**. Fallback chains should be code you can read, not magic SQL. The database does what it does well (filtering, sorting, joining), and the application layer handles what it does well (orchestration, caching, graceful degradation).

This approach scales: add new sources without rewriting queries, debug with clear source metadata, and test each layer independently.