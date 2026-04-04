import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { MapPin, Building2, ChevronRight, ChevronLeft, Search, Trophy, TrendingUp, Users, AlertTriangle, CheckCircle, XCircle, ArrowUpDown } from 'lucide-react';

const PAGE_SIZE = 100;

const formatCurrency = (val) => {
  if (!val) return '-';
  if (val >= 1000000) return `${(val / 1000000).toFixed(1)}M RON`;
  if (val >= 1000) return `${Math.round(val / 1000)}K RON`;
  return `${val.toLocaleString('ro-RO')} RON`;
};

const JudetPage = () => {
  const { judetSlug } = useParams();
  const [tab, setTab] = useState('top');
  const [localities, setLocalities] = useState([]);
  const [judetName, setJudetName] = useState('');
  const [totalCompanies, setTotalCompanies] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Top firme state
  const [topCompanies, setTopCompanies] = useState([]);
  const [topTotal, setTopTotal] = useState(0);
  const [topPage, setTopPage] = useState(1);
  const [topLoading, setTopLoading] = useState(false);
  const [topSort, setTopSort] = useState('cifra_afaceri');

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    const fetchLocalities = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${API_URL}/api/locations/judet/${judetSlug}?limit=500`);
        if (res.ok) {
          const data = await res.json();
          setLocalities(data.localities || []);
          setJudetName(data.judet || '');
          setTotalCompanies(data.total_companies || 0);
        }
      } catch (err) {
        console.error('Failed to load localities:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchLocalities();
  }, [API_URL, judetSlug]);

  const loadTopCompanies = useCallback(async (pageNum = 1, sortBy = 'cifra_afaceri') => {
    setTopLoading(true);
    try {
      const skip = (pageNum - 1) * PAGE_SIZE;
      const res = await fetch(`${API_URL}/api/locations/judet/${judetSlug}/top-firme?skip=${skip}&limit=${PAGE_SIZE}&sort=${sortBy}`);
      if (res.ok) {
        const data = await res.json();
        setTopCompanies(data.companies || []);
        setTopTotal(data.total || 0);
        if (data.judet) setJudetName(data.judet);
      }
    } catch (err) {
      console.error('Failed to load top companies:', err);
    } finally {
      setTopLoading(false);
    }
  }, [API_URL, judetSlug]);

  useEffect(() => {
    if (tab === 'top') {
      loadTopCompanies(1, topSort);
      setTopPage(1);
    }
  }, [tab, topSort, loadTopCompanies]);

  const handleTopPage = (p) => {
    setTopPage(p);
    loadTopCompanies(p, topSort);
    window.scrollTo(0, 0);
  };

  const topTotalPages = Math.ceil(topTotal / PAGE_SIZE);

  const filtered = search
    ? localities.filter(l => l.name.toLowerCase().includes(search.toLowerCase()))
    : localities;

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6" data-testid="breadcrumb">
          <Link to="/" className="hover:text-primary">Acasa</Link>
          <ChevronRight className="w-3 h-3" />
          <Link to="/judete" className="hover:text-primary">Judete</Link>
          <ChevronRight className="w-3 h-3" />
          <span className="text-foreground font-medium">{judetName}</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2" data-testid="judet-title">
            Firme din {judetName}
          </h1>
          <p className="text-muted-foreground">
            {totalCompanies.toLocaleString('ro-RO')} firme in {localities.length} localitati
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-muted/50 p-1 rounded-lg w-fit" data-testid="page-tabs">
          <button
            onClick={() => setTab('top')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'top' ? 'bg-card text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
            data-testid="tab-top-firme"
          >
            <Trophy className="w-4 h-4" />
            Top Firme
          </button>
          <button
            onClick={() => setTab('localitati')}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === 'localitati' ? 'bg-card text-primary shadow-sm' : 'text-muted-foreground hover:text-foreground'}`}
            data-testid="tab-localitati"
          >
            <MapPin className="w-4 h-4" />
            Localitati ({localities.length})
          </button>
        </div>

        {/* Top Firme Tab */}
        {tab === 'top' && (
          <>
            {/* Sort */}
            <div className="flex items-center gap-3 mb-4" data-testid="top-sort">
              <ArrowUpDown className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Sorteaza dupa:</span>
              {[
                { key: 'cifra_afaceri', label: 'Cifra de afaceri' },
                { key: 'profit', label: 'Profit net' },
                { key: 'angajati', label: 'Nr. angajati' },
              ].map(s => (
                <button
                  key={s.key}
                  onClick={() => setTopSort(s.key)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${topSort === s.key ? 'bg-primary text-primary-foreground border-primary' : 'border-border hover:bg-muted text-muted-foreground'}`}
                  data-testid={`sort-${s.key}`}
                >
                  {s.label}
                </button>
              ))}
            </div>

            {topLoading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : (
              <>
                <div className="bg-card border border-border rounded-xl overflow-hidden" data-testid="top-companies-table">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border bg-muted/50">
                        <th className="text-center px-3 py-3 text-xs font-medium text-muted-foreground uppercase w-14">#</th>
                        <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase">Denumire</th>
                        <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden md:table-cell">Localitate</th>
                        <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden lg:table-cell">CAEN</th>
                        <th className="text-right px-4 py-3 text-xs font-medium text-muted-foreground uppercase">Cifra afaceri</th>
                        <th className="text-right px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden sm:table-cell">Profit</th>
                        <th className="text-center px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden md:table-cell">Angajati</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topCompanies.map((c) => (
                        <tr key={c.cui} className={`border-b border-border last:border-0 hover:bg-muted/30 transition-colors ${c.rank <= 3 ? 'bg-amber-50/50' : ''}`}>
                          <td className="text-center px-3 py-3">
                            {c.rank <= 3 ? (
                              <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold text-white ${c.rank === 1 ? 'bg-amber-500' : c.rank === 2 ? 'bg-gray-400' : 'bg-amber-700'}`}>
                                {c.rank}
                              </span>
                            ) : (
                              <span className="text-sm text-muted-foreground font-mono">{c.rank}</span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <Link to={`/firma/${c.slug}`} className="text-sm font-medium text-primary hover:underline" data-testid={`top-company-${c.cui}`}>
                              {c.denumire}
                            </Link>
                            <div className="text-xs text-muted-foreground font-mono mt-0.5">CUI: {c.cui}</div>
                          </td>
                          <td className="px-4 py-3 text-xs text-muted-foreground hidden md:table-cell">{c.localitate || '-'}</td>
                          <td className="px-4 py-3 text-xs text-muted-foreground hidden lg:table-cell">
                            {c.anaf_cod_caen ? (
                              <Link to={`/caen/${c.anaf_cod_caen}`} className="hover:text-primary font-mono">{c.anaf_cod_caen}</Link>
                            ) : '-'}
                          </td>
                          <td className="px-4 py-3 text-right text-sm font-medium">{formatCurrency(c.mf_cifra_afaceri)}</td>
                          <td className={`px-4 py-3 text-right text-sm hidden sm:table-cell ${c.mf_profit_net < 0 ? 'text-red-600' : ''}`}>
                            {formatCurrency(c.mf_profit_net)}
                          </td>
                          <td className="px-4 py-3 text-center text-sm hidden md:table-cell">{c.mf_numar_angajati || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {topTotalPages > 1 && (
                  <div className="flex items-center justify-between mt-6" data-testid="top-pagination">
                    <button
                      onClick={() => handleTopPage(topPage - 1)}
                      disabled={topPage <= 1}
                      className="flex items-center gap-1 px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="w-4 h-4" /> Inapoi
                    </button>
                    <span className="text-sm text-muted-foreground">
                      Pagina {topPage} din {topTotalPages.toLocaleString('ro-RO')} ({topTotal.toLocaleString('ro-RO')} firme)
                    </span>
                    <button
                      onClick={() => handleTopPage(topPage + 1)}
                      disabled={topPage >= topTotalPages}
                      className="flex items-center gap-1 px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      Inainte <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </>
            )}
          </>
        )}

        {/* Localitati Tab */}
        {tab === 'localitati' && (
          <>
            <div className="relative mb-6 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Cauta localitate..."
                className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-background focus:outline-none focus:border-primary text-sm"
                data-testid="locality-search"
              />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3" data-testid="localities-grid">
              {filtered.map((loc) => (
                <Link
                  key={loc.slug}
                  to={`/judet/${judetSlug}/${loc.slug}`}
                  className="group bg-card border border-border rounded-lg p-4 hover:border-primary/50 hover:shadow-md transition-all"
                  data-testid={`locality-${loc.slug}`}
                >
                  <div className="flex items-start gap-2">
                    <Building2 className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                    <div className="min-w-0">
                      <div className="font-medium text-sm group-hover:text-primary transition-colors truncate">
                        {loc.name}
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        {loc.company_count.toLocaleString('ro-RO')} firme
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>

            {filtered.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                Nu s-au gasit localitati pentru "{search}"
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default JudetPage;
