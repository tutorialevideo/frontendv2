const API_URL = process.env.REACT_APP_BACKEND_URL || '';

export const api = {
  // Search - tries Elasticsearch first, falls back to MongoDB
  searchSuggest: async (query) => {
    const res = await fetch(`${API_URL}/api/search/suggest?q=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error('Search suggest failed');
    return res.json();
  },

  search: async (params) => {
    // Try Elasticsearch first
    try {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value) searchParams.append(key, value);
      });
      
      const esRes = await fetch(`${API_URL}/api/elasticsearch/search/simple?${searchParams}`);
      if (esRes.ok) {
        const esData = await esRes.json();
        if (esData.success && esData.data && esData.data.pagination.total > 0) {
          return {
            results: esData.data.results,
            total: esData.data.pagination.total,
            page: esData.data.pagination.page,
            pages: esData.data.pagination.pages,
            search_engine: 'elasticsearch'
          };
        }
      }
    } catch (esError) {
      console.log('Elasticsearch not available, falling back to MongoDB');
    }
    
    // Fallback to MongoDB search (also when ES returns 0 results)
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) searchParams.append(key, value);
    });
    const res = await fetch(`${API_URL}/api/search?${searchParams}`);
    if (!res.ok) throw new Error('Search failed');
    const data = await res.json();
    return { ...data, search_engine: 'mongodb' };
  },

  // Direct Elasticsearch search (for advanced use)
  searchElasticsearch: async (params) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value) searchParams.append(key, value);
    });
    const res = await fetch(`${API_URL}/api/elasticsearch/search/simple?${searchParams}`);
    if (!res.ok) throw new Error('Elasticsearch search failed');
    return res.json();
  },

  // Company
  getCompanyBySlug: async (slug) => {
    const res = await fetch(`${API_URL}/api/company/slug/${slug}`);
    if (!res.ok) throw new Error('Company not found');
    return res.json();
  },

  getCompanyByCUI: async (cui) => {
    const res = await fetch(`${API_URL}/api/company/cui/${cui}`);
    if (!res.ok) throw new Error('Company not found');
    return res.json();
  },

  // Geo
  getJudete: async () => {
    const res = await fetch(`${API_URL}/api/geo/judete`);
    if (!res.ok) throw new Error('Failed to fetch counties');
    return res.json();
  },

  getLocalitati: async (judet) => {
    const url = judet 
      ? `${API_URL}/api/geo/localitati?judet=${encodeURIComponent(judet)}`
      : `${API_URL}/api/geo/localitati`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch localities');
    return res.json();
  },

  // CAEN
  getTopCaenCodes: async (limit = 50) => {
    const res = await fetch(`${API_URL}/api/caen/top?limit=${limit}`);
    if (!res.ok) throw new Error('Failed to fetch CAEN codes');
    return res.json();
  },

  // Stats
  getStats: async () => {
    const res = await fetch(`${API_URL}/api/stats/overview`);
    if (!res.ok) throw new Error('Failed to fetch stats');
    return res.json();
  },
};

export default api;