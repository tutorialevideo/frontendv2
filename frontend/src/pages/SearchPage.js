import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { useSearchParams } from 'react-router-dom';
import { Search, Building2, ChevronRight, X, Phone, Printer } from 'lucide-react';
import { useSeoTemplate } from '../hooks/useSeoTemplate';
import { Link } from 'react-router-dom';
import api from '../services/api';

// Helper to create slug from judet name
const judetSlug = (judet) => {
  if (!judet) return '';
  return judet.toLowerCase()
    .replace(/ș|ş/g, 's').replace(/ț|ţ/g, 't')
    .replace(/ă/g, 'a').replace(/â|î/g, 'i')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
};

const localitateSlug = (loc) => {
  if (!loc) return '';
  return loc.toLowerCase()
    .replace(/ș|ş/g, 's').replace(/ț|ţ/g, 't')
    .replace(/ă/g, 'a').replace(/â|î/g, 'i')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
};

const SearchPage = ({ initialFilters = {} }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [query, setQuery] = useState(initialFilters.q || searchParams.get('q') || '');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  
  // Filters
  const [selectedJudet, setSelectedJudet] = useState(initialFilters.judet || searchParams.get('judet') || '');
  const [selectedLocalitate, setSelectedLocalitate] = useState(initialFilters.localitate || searchParams.get('localitate') || '');
  const [selectedCaen, setSelectedCaen] = useState(initialFilters.caen || searchParams.get('caen') || '');
  const [judete, setJudete] = useState([]);
  const [localitati, setLocalitati] = useState([]);
  
  // Check if this is a nested component (used by JudetPage, etc)
  const isNested = Object.keys(initialFilters).length > 0;

  useEffect(() => {
    loadJudete();
  }, []);

  useEffect(() => {
    if (selectedJudet) {
      loadLocalitati(selectedJudet);
    } else {
      setLocalitati([]);
    }
  }, [selectedJudet]);

  // Load judete on mount
  useEffect(() => {
    loadJudete();
  }, []);

  useEffect(() => {
    const q = searchParams.get('q') || '';
    const judet = searchParams.get('judet') || '';
    const localitate = searchParams.get('localitate') || '';
    const caen = searchParams.get('caen') || '';
    
    setQuery(q);
    setSelectedJudet(judet);
    setSelectedLocalitate(localitate);
    setSelectedCaen(caen);
    
    performSearch(q, judet, localitate, caen, 1);
  }, [searchParams]);

  const loadJudete = async () => {
    try {
      const data = await api.getJudete();
      setJudete(data.judete || []);
    } catch (error) {
      console.error('Failed to load judete:', error);
    }
  };

  const loadLocalitati = async (judet) => {
    try {
      const data = await api.getLocalitati(judet);
      setLocalitati(data.localitati || []);
    } catch (error) {
      console.error('Failed to load localitati:', error);
    }
  };

  const performSearch = async (q, judet, localitate, caen, pageNum) => {
    setLoading(true);
    try {
      const data = await api.search({
        q,
        judet,
        localitate,
        caen,
        page: pageNum,
        limit: 20
      });
      setResults(data.results || []);
      setTotal(data.total || 0);
      setPage(pageNum);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    updateSearchParams({ q: query });
  };

  const updateSearchParams = (updates) => {
    const params = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    });
    setSearchParams(params);
  };

  const clearFilter = (filterName) => {
    const updates = { [filterName]: '' };
    if (filterName === 'judet') {
      updates.localitate = '';
      setSelectedLocalitate('');
      setLocalitati([]);
    }
    updateSearchParams(updates);
  };

  // SEO template
  const { title: seoTitle, description: seoDescription, index: seoIndex } = useSeoTemplate('search', {
    QUERY: query || 'toate firmele'
  });

  // JSON-LD for Search Results
  const searchResultsSchema = results.length > 0 ? {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": `Rezultate căutare: ${query || 'firme'}`,
    "description": `${total} firme găsite pentru căutarea "${query || 'toate firmele'}"`,
    "numberOfItems": results.length,
    "itemListElement": results.slice(0, 10).map((company, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "item": {
        "@type": "Organization",
        "name": company.denumire,
        "identifier": company.cui,
        "address": {
          "@type": "PostalAddress",
          "addressLocality": company.localitate || '',
          "addressRegion": company.judet || '',
          "addressCountry": "RO"
        }
      }
    }))
  } : null;

  return (
    <>
      {!isNested && (
        <Helmet>
          <title>{seoTitle || `Cautare firme${query ? ` - ${query}` : ''} | RapoarteFirme`}</title>
          <meta name="description" content={seoDescription || `Cautare firme din Romania${query ? `: ${query}` : ''}. Gaseste informatii complete: CUI, bilant, cifra de afaceri, contact, dosare instanta.`} />
          <meta name="keywords" content={`cautare firme${query ? `, ${query}` : ''}, informatii firma, cui, bilant, romania`} />
          <meta name="robots" content={seoIndex !== false && !query ? "index, follow" : "noindex, follow"} />
          <meta name="publisher" content="RapoarteFirme.ro" />
          <link rel="canonical" href={`https://rapoartefirme.ro/search${query ? `?q=${encodeURIComponent(query)}` : ''}`} />
          {searchResultsSchema && (
            <script type="application/ld+json">
              {JSON.stringify(searchResultsSchema)}
            </script>
          )}
        </Helmet>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="mb-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Caută firme..."
              className="w-full pl-12 pr-4 py-3 text-base border border-border rounded-lg focus:outline-none focus:border-primary transition-colors bg-card"
              data-testid="search-input"
            />
          </div>
        </form>

        {/* Active Filters */}
        {(selectedJudet || selectedLocalitate || selectedCaen) && (
          <div className="flex flex-wrap gap-2 mb-6">
            {selectedJudet && (
              <button
                onClick={() => clearFilter('judet')}
                className="inline-flex items-center space-x-1 px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-lg hover:bg-primary/20 transition-colors"
                data-testid="filter-chip-judet"
              >
                <span>Județ: {selectedJudet}</span>
                <X className="w-3 h-3" />
              </button>
            )}
            {selectedLocalitate && (
              <button
                onClick={() => clearFilter('localitate')}
                className="inline-flex items-center space-x-1 px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-lg hover:bg-primary/20 transition-colors"
                data-testid="filter-chip-localitate"
              >
                <span>Localitate: {selectedLocalitate}</span>
                <X className="w-3 h-3" />
              </button>
            )}
            {selectedCaen && (
              <button
                onClick={() => clearFilter('caen')}
                className="inline-flex items-center space-x-1 px-3 py-1.5 bg-primary/10 text-primary text-sm rounded-lg hover:bg-primary/20 transition-colors"
                data-testid="filter-chip-caen"
              >
                <span>CAEN: {selectedCaen}</span>
                <X className="w-3 h-3" />
              </button>
            )}
          </div>
        )}

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <aside className="lg:col-span-1 space-y-6">
            <div className="bg-card border border-border rounded-xl p-4">
              <h3 className="text-sm font-semibold mb-4">Filtre</h3>
              
              {/* Județ Filter */}
              <div className="mb-4">
                <label className="text-xs font-medium text-muted-foreground block mb-2">Județ</label>
                <select
                  value={selectedJudet}
                  onChange={(e) => updateSearchParams({ judet: e.target.value, localitate: '' })}
                  className="w-full px-3 py-2 text-sm border border-border rounded-lg focus:outline-none focus:border-primary bg-background"
                  data-testid="filter-judet"
                >
                  <option value="">Toate județele</option>
                  {judete.map((j, idx) => (
                    <option key={idx} value={j.judet}>{j.judet} ({j.count})</option>
                  ))}
                </select>
              </div>

              {/* Localitate Filter */}
              {selectedJudet && localitati.length > 0 && (
                <div className="mb-4">
                  <label className="text-xs font-medium text-muted-foreground block mb-2">Localitate</label>
                  <select
                    value={selectedLocalitate}
                    onChange={(e) => updateSearchParams({ localitate: e.target.value })}
                    className="w-full px-3 py-2 text-sm border border-border rounded-lg focus:outline-none focus:border-primary bg-background"
                    data-testid="filter-localitate"
                  >
                    <option value="">Toate localitățile</option>
                    {localitati.slice(0, 100).map((l, idx) => (
                      <option key={idx} value={l.localitate}>{l.localitate} ({l.count})</option>
                    ))}
                  </select>
                </div>
              )}

              {/* CAEN Filter */}
              <div>
                <label className="text-xs font-medium text-muted-foreground block mb-2">Cod CAEN</label>
                <input
                  type="text"
                  value={selectedCaen}
                  onChange={(e) => setSelectedCaen(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && updateSearchParams({ caen: selectedCaen })}
                  onBlur={() => updateSearchParams({ caen: selectedCaen })}
                  placeholder="Ex: 4120"
                  className="w-full px-3 py-2 text-sm border border-border rounded-lg focus:outline-none focus:border-primary bg-background"
                  data-testid="filter-caen"
                />
              </div>
            </div>
          </aside>

          {/* Results */}
          <main className="lg:col-span-3">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-sm text-muted-foreground" data-testid="results-count">
                {loading ? 'Se caută...' : `${total.toLocaleString('ro-RO')} rezultate`}
              </p>
            </div>

            <div className="space-y-1.5">
              {loading ? (
                <div className="text-center py-12 text-muted-foreground">Se încarcă...</div>
              ) : results.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground" data-testid="no-results">
                  <Building2 className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p>Nu am găsit rezultate pentru această căutare</p>
                </div>
              ) : (
                results.map((company, index) => (
                  <Link
                    key={index}
                    to={`/firma/${company.slug}`}
                    className="flex items-center gap-3 bg-card border border-border rounded-lg px-4 py-2.5 hover:border-primary/50 hover:shadow-sm transition-all group"
                    data-testid={`result-${index}`}
                  >
                    {/* Company name + status */}
                    <div className="flex-1 min-w-0 flex items-center gap-2">
                      <span className="text-sm font-semibold truncate group-hover:text-primary transition-colors" data-testid={`result-link-${index}`}>
                        {company.denumire}
                      </span>
                      <span className={`shrink-0 text-[9px] font-bold px-1 py-px rounded ${
                        company.anaf_stare?.includes('INREGISTRAT')
                          ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {company.anaf_stare?.includes('INREGISTRAT') ? 'ACTIV' : 'INACTIV'}
                      </span>
                    </div>

                    {/* Meta: CUI, location links, contact icons, financials */}
                    <div className="hidden md:flex items-center gap-3 shrink-0 text-xs text-muted-foreground">
                      <span className="font-mono text-[11px]">{company.cui}</span>

                      {company.judet && (
                        <span
                          className="text-primary hover:underline cursor-pointer"
                          onClick={e => { e.preventDefault(); window.location.href = `/judet/${judetSlug(company.judet)}`; }}
                          data-testid={`result-jud-${index}`}
                        >
                          {company.localitate ? `${company.localitate}, ${company.judet}` : company.judet}
                        </span>
                      )}

                      {/* Contact icons */}
                      {company.anaf_telefon && (
                        <span
                          className="text-green-600"
                          title={company.anaf_telefon}
                          data-testid={`result-phone-${index}`}
                        >
                          <Phone className="w-3.5 h-3.5" />
                        </span>
                      )}
                      {company.anaf_fax && (
                        <span className="text-slate-400" title={`Fax: ${company.anaf_fax}`}>
                          <Printer className="w-3.5 h-3.5" />
                        </span>
                      )}
                    </div>

                    <ChevronRight className="w-4 h-4 shrink-0 text-muted-foreground/50 group-hover:text-primary transition-colors" />
                  </Link>
                ))
              )}
            </div>
          </main>
        </div>
      </div>
    </>
  );
};

export default SearchPage;