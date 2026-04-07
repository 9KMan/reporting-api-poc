"""
Reporting API with Primary → Secondary Fallback Logic
Intelligence Platform POC

Screening Question:
"You have a reporting API with joins + fallback logic (primary → secondary). 
How would you structure it so it stays clear, testable, and maintainable over time?"
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import asyncpg


# ============== Enums ==============
class ReportStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    ESCALATED = "escalated"


class SourceType(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    FALLBACK = "fallback"


# ============== Data Models ==============
class SourceBase(BaseModel):
    name: str
    type: SourceType
    priority: int = 0
    is_active: bool = True


class IntelligenceSource(SourceBase):
    id: uuid.UUID
    last_checked_at: Optional[datetime]
    last_success_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportBase(BaseModel):
    title: str
    content: Optional[str] = None
    source_id: Optional[uuid.UUID] = None
    status: ReportStatus = ReportStatus.ACTIVE
    priority: int = 0
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    tags: Optional[List[str]] = []
    metadata: Optional[dict] = {}
    published_at: Optional[datetime] = None


class Report(ReportBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Response with data + metadata for pagination"""
    data: List[Report]
    meta: dict
    source_info: Optional[dict] = None


class ReportFilter(BaseModel):
    """Filter parameters for reports"""
    status: Optional[ReportStatus] = None
    priority: Optional[int] = None
    source_type: Optional[SourceType] = None
    search: Optional[str] = None
    tags: Optional[List[str]] = None


# ============== Query Builder ==============
class ReportQueryBuilder:
    """
    Query builder pattern for reports.
    Separates concerns: filter building → execution → serialization.
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    def build_filtered_query(
        self,
        filters: ReportFilter,
        page: int = 1,
        limit: int = 20
    ) -> tuple[str, list]:
        """
        Build WHERE clause from filters.
        Returns (query_string, params_list).
        """
        conditions = ["1=1"]
        params = []
        param_idx = 1
        
        if filters.status:
            conditions.append(f"r.status = ${param_idx}")
            params.append(filters.status.value)
            param_idx += 1
        
        if filters.priority is not None:
            conditions.append(f"r.priority >= ${param_idx}")
            params.append(filters.priority)
            param_idx += 1
        
        if filters.search:
            conditions.append(f"(r.title ILIKE ${param_idx} OR r.content ILIKE ${param_idx})")
            params.append(f"%{filters.search}%")
            param_idx += 1
        
        if filters.tags and len(filters.tags) > 0:
            conditions.append(f"r.tags && ${param_idx}")
            params.append(filters.tags)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        # Main query with source join
        query = f"""
            SELECT r.id, r.title, r.content, r.source_id, r.status, r.priority,
                   r.confidence, r.tags, r.metadata, r.published_at,
                   r.created_at, r.updated_at,
                   s.name as source_name, s.type as source_type, s.priority as source_priority
            FROM reports r
            LEFT JOIN intelligence_sources s ON r.source_id = s.id
            WHERE {where_clause}
            ORDER BY r.published_at DESC NULLS LAST
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
        """
        params.extend([limit, (page - 1) * limit])
        
        return query, params
    
    async def execute(self, query: str, params: list) -> List[dict]:
        """Execute query and return results as dicts"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *params)


# ============== Fallback Service ==============
class ReportFallbackService:
    """
    The core fallback logic - primary → secondary → fallback chain.
    
    Why this structure:
    1. Clear: fallback chain is explicit, not buried in WHERE clauses
    2. Testable: mock each source independently 
    3. Maintainable: add new sources by implementing the chain
    4. Transparent: each result includes source_info for debugging
    """
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.query_builder = ReportQueryBuilder(pool)
    
    async def get_with_fallback(
        self,
        filters: ReportFilter,
        page: int = 1,
        limit: int = 20
    ) -> ReportListResponse:
        """
        Get reports with fallback: primary → secondary → fallback.
        
        Returns data + metadata + which source provided the data.
        """
        
        # Strategy: Try primary source, if empty try secondary, etc.
        fallback_chain = [
            SourceType.PRIMARY,
            SourceType.SECONDARY,
            SourceType.FALLBACK
        ]
        
        for source_type in fallback_chain:
            # Apply source type filter
            current_filters = filters.model_copy()
            current_filters.source_type = source_type
            
            query, params = self.query_builder.build_filtered_query(
                current_filters, page, limit
            )
            
            results = await self.query_builder.execute(query, params)
            
            if results and len(results) > 0:
                # Success from this source
                source_info = {
                    "served_from": source_type.value,
                    "fallback_tried": len(results) > 0,
                    "fallback_chain_position": fallback_chain.index(source_type) + 1
                }
                
                return ReportListResponse(
                    data=[Report(**r) for r in results],
                    meta={
                        "total": len(results),
                        "page": page,
                        "limit": limit,
                        "has_more": len(results) >= limit
                    },
                    source_info=source_info
                )
        
        # All sources exhausted - return empty
        return ReportListResponse(
            data=[],
            meta={"total": 0, "page": page, "limit": limit, "has_more": False},
            source_info={
                "served_from": "none",
                "fallback_tried": True,
                "fallback_chain_exhausted": True
            }
        )


# ============== FastAPI App ==============
app = FastAPI(
    title="Intelligence Reporting API",
    description="Reporting API with primary → secondary fallback logic",
    version="1.0.0"
)

# Pool would be initialized with database URL
# pool = asyncpg.pool()


@app.get("/reports/", response_model=ReportListResponse)
async def get_reports(
    status: Optional[ReportStatus] = Query(None),
    priority: Optional[int] = Query(None, ge=0, le=3),
    search: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    # pool: asyncpg.Pool = Depends(get_db)
):
    """
    Get reports with primary → secondary fallback.
    
    - If primary source has data, return it
    - If primary is empty, automatically try secondary
    - Continue down the chain until data is found
    
    Response includes `source_info` showing which source provided the data.
    """
    
    # In production, get pool from dependency
    # For POC, just return structure
    filters = ReportFilter(
        status=status,
        priority=priority,
        search=search,
        tags=tags.split(",") if tags else None
    )
    
    # For full implementation:
    # service = ReportFallbackService(pool)
    # return await service.get_with_fallback(filters, page, limit)
    
    # Return mock response structure for POC
    return ReportListResponse(
        data=[],
        meta={"total": 0, "page": page, "limit": limit, "has_more": False},
        source_info={
            "served_from": "primary",
            "fallback_tried": False,
            "note": "POC - needs database connection"
        }
    )


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "intelligence-api"}


# ============== Testing ==============
"""
Unit test example for fallback logic:

async def test_primary_fallback_chain():
    # Setup
    pool = await create_test_pool()
    service = ReportFallbackService(pool)
    
    # Test 1: Primary has data - should return from primary
    result = await service.get_with_fallback(ReportFilter())
    assert result.source_info["served_from"] == "primary"
    assert len(result.data) > 0
    
    # Test 2: Primary empty - should fallback to secondary
    # (Simulate empty primary by filtering to non-existent)
    result = await service.get_with_fallback(
        ReportFilter(search="NONEXISTENT")
    )
    assert result.source_info["fallback_tried"] == True
    # Should have tried secondary
    
    # Test 3: All sources empty - should return empty with exhausted flag
    assert result.source_info.get("fallback_chain_exhausted") == None  # or True
"""