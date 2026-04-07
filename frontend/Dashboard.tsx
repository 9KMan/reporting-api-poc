// Reporting API - React Frontend POC
// Intelligence Dashboard with Filtering + Pagination

import React, { useState, useEffect } from 'react';
import { create } from 'jotai';
import { atomWithQuery } from 'jotai/query';

// ============== Types ==============
interface Report {
  id: string;
  title: string;
  content: string;
  source_id: string;
  status: 'active' | 'archived' | 'draft' | 'escalated';
  priority: number;
  confidence: number;
  tags: string[];
  metadata: Record<string, any>;
  published_at: string;
  created_at: string;
  // Source join fields
  source_name?: string;
  source_type?: string;
  source_priority?: number;
}

interface ReportFilter {
  status?: string;
  priority?: number;
  search?: string;
  tags?: string;
}

interface ReportListResponse {
  data: Report[];
  meta: {
    total: number;
    page: number;
    limit: number;
    has_more: boolean;
  };
  source_info?: {
    served_from: string;
    fallback_tried: boolean;
    fallback_chain_position?: number;
  };
}

// ============== Atoms ==============
const reportsAtom = atomWithQuery((get) => ({
  queryKey: ['reports', 'current'],
  queryFn: async () => {
    const state = get(reportsFilterAtom);
    const params = new URLSearchParams();
    
    if (state.status) params.set('status', state.status);
    if (state.priority) params.set('priority', String(state.priority));
    if (state.search) params.set('search', state.search);
    if (state.tags) params.set('tags', state.tags);
    params.set('page', String(state.page));
    params.set('limit', String(state.limit));
    
    const res = await fetch(`/api/reports/?${params}`);
    const data: ReportListResponse = await res.json();
    return data;
  },
}));

const reportsFilterAtom = atom<ReportFilter & { page: number; limit: number }>({
  page: 1,
  limit: 20,
});

// ============== Components ==============

// Status Badge
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const colors = {
    active: 'bg-green-100 text-green-800',
    archived: 'bg-gray-100 text-gray-800',
    draft: 'bg-yellow-100 text-yellow-800',
    escalated: 'bg-red-100 text-red-800',
  };
  
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status as keyof typeof colors] || colors.active}`}>
      {status}
    </span>
  );
};

// Priority Indicator
const PriorityIndicator: React.FC<{ priority: number }> = ({ priority }) => {
  const labels = ['Low', 'Medium', 'High', 'Critical'];
  const colors = ['bg-gray-400', 'bg-yellow-500', 'bg-orange-500', 'bg-red-600'];
  
  return (
    <span className={`w-2 h-2 rounded-full inline-block mr-2 ${colors[priority]}`} 
          title={labels[priority]} />
  );
};

// Filter Bar
const FilterBar: React.FC = () => {
  const [filter, setFilter] = useAtom(reportsFilterAtom);
  
  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilter({ ...filter, status: e.target.value || undefined, page: 1 });
  };
  
  const handlePriorityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilter({ ...filter, priority: Number(e.target.value) || undefined, page: 1 });
  };
  
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilter({ ...filter, search: e.target.value || undefined, page: 1 });
  };
  
  return (
    <div className="flex flex-wrap gap-4 p-4 bg-gray-50 border-b">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
        <select 
          value={filter.status || ''} 
          onChange={handleStatusChange}
          className="border rounded px-3 py-2"
        >
          <option value="">All</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
          <option value="draft">Draft</option>
          <option value="escalated">Escalated</option>
        </select>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
        <select 
          value={filter.priority ?? ''} 
          onChange={handlePriorityChange}
          className="border rounded px-3 py-2"
        >
          <option value="">All</option>
          <option value="0">Low</option>
          <option value="1">Medium</option>
          <option value="2">High</option>
          <option value="3">Critical</option>
        </select>
      </div>
      
      <div className="flex-1">
        <label className="block text-sm font-medium text-gray-700 mb-1">Search</label>
        <input 
          type="text"
          value={filter.search || ''}
          onChange={handleSearchChange}
          placeholder="Search reports..."
          className="border rounded px-3 py-2 w-full"
        />
      </div>
    </div>
  );
};

// Report Card
const ReportCard: React.FC<{ report: Report }> = ({ report }) => {
  return (
    <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center">
          <PriorityIndicator priority={report.priority} />
          <h3 className="font-semibold text-lg">{report.title}</h3>
        </div>
        <StatusBadge status={report.status} />
      </div>
      
      <p className="text-gray-600 text-sm mb-3 line-clamp-2">
        {report.content}
      </p>
      
      <div className="flex flex-wrap gap-2 text-sm text-gray-500">
        <span>{report.source_name}</span>
        <span>•</span>
        <span>{report.confidence ? `${Math.round(report.confidence * 100)}% confidence` : 'N/A'}</span>
        <span>•</span>
        <span>{new Date(report.published_at).toLocaleDateString()}</span>
      </div>
      
      {report.tags && report.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {report.tags.map((tag, i) => (
            <span key={i} className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

// Main Dashboard
const ReportsDashboard: React.FC = () => {
  const [response] = useAtom(reportsAtom);
  const [filter, setFilter] = useAtom(reportsFilterAtom);
  
  const { data, meta, source_info } = response || { data: [], meta: {}, source_info: {} };
  
  const handlePrevPage = () => {
    if (filter.page > 1) setFilter({ ...filter, page: filter.page - 1 });
  };
  
  const handleNextPage = () => {
    setFilter({ ...filter, page: filter.page + 1 });
  };
  
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gray-900 text-white p-4">
        <h1 className="text-xl font-bold">Intelligence Reports</h1>
        <p className="text-gray-400 text-sm">Intelligence Platform Dashboard</p>
      </header>
      
      {/* Filter Bar */}
      <FilterBar />
      
      {/* Source Info Banner */}
      {source_info && (
        <div className="bg-blue-50 border-b px-4 py-2 flex items-center gap-2">
          <span className="text-sm text-gray-600">Data from:</span>
          <span className="font-medium text-blue-700">{source_info.served_from}</span>
          {source_info.fallback_tried && (
            <span className="text-xs text-gray-500">
              (fallback position: {source_info.fallback_chain_position})
            </span>
          )}
        </div>
      )}
      
      {/* Reports List */}
      <div className="p-4">
        {data.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No reports found
          </div>
        ) : (
          <div className="grid gap-4">
            {data.map((report) => (
              <ReportCard key={report.id} report={report} />
            ))}
          </div>
        )}
      </div>
      
      {/* Pagination */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4 flex justify-between items-center">
        <span className="text-sm text-gray-600">
          Showing {((filter.page - 1) * filter.limit) + 1}-{Math.min(filter.page * filter.limit, meta.total)} of {meta.total}
        </span>
        <div className="flex gap-2">
          <button 
            onClick={handlePrevPage}
            disabled={filter.page === 1}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Previous
          </button>
          <button 
            onClick={handleNextPage}
            disabled={!meta.has_more}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default ReportsDashboard;