import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRight, Search, ChevronLeft, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

const LocalitatePage = () => {
  const { judetSlug, localitateSlug } = useParams();
  const [companies, setCompanies] = useState([]);
  const [judetName, setJudetName] = useState('');
  const [localitateName, setLocalitateName] = useState('');
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const PAGE_SIZE = 50;
  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  const loadCompanies = useCallback(async (pageNum = 1, q = '') => {
    setLoading(true);
    try {
      const skip = (pageNum - 1) * PAGE_SIZE;
      const res = await fetch(
        `${API_URL}/api/locations/judet/${judetSlug}/${localitateSlug}?skip=${skip}&limit=${PAGE_SIZE}&q=${encodeURIComponent(q)}`
      );
      if (res.ok) {
        const data = await res.json();
        setCompanies(data.companies || []);
        setTotal(data.total || 0);
        setJudetName(data.judet || '');
        setLocalitateName(data.localitate || '');
      }
    } catch (err) {
      console.error('Failed to load companies:', err);
    } finally {
      setLoading(false);
    }
  }, [API_URL, judetSlug, localitateSlug]);

  useEffect(() => {
    loadCompanies(1, '');
  }, [loadCompanies]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadCompanies(1, search);
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handlePage = (p) => {
    setPage(p);
    loadCompanies(p, search);
    window.scrollTo(0, 0);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6 flex-wrap" data-testid="breadcrumb">
          <Link to="/" className="hover:text-primary">Acasa</Link>
          <ChevronRight className="w-3 h-3" />
          <Link to="/judete" className="hover:text-primary">Judete</Link>
          <ChevronRight className="w-3 h-3" />
          <Link to={`/judet/${judetSlug}`} className="hover:text-primary">{judetName}</Link>
          <ChevronRight className="w-3 h-3" />
          <span className="text-foreground font-medium">{localitateName}</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2" data-testid="localitate-title">
            Firme din {localitateName}, {judetName}
          </h1>
          <p className="text-muted-foreground">
            {total.toLocaleString('ro-RO')} firme inregistrate
          </p>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex gap-2 mb-6 max-w-lg">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Cauta firma dupa denumire sau CUI..."
              className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-background focus:outline-none focus:border-primary text-sm"
              data-testid="company-search"
            />
          </div>
          <button type="submit" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:bg-primary/90">
            Cauta
          </button>
        </form>

        {/* Companies list */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <>
            <div className="bg-card border border-border rounded-xl overflow-hidden" data-testid="companies-table">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase">Denumire</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase">CUI</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden md:table-cell">CAEN</th>
                    <th className="text-center px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden sm:table-cell">Stare</th>
                    <th className="text-right px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden lg:table-cell">Cifra afaceri</th>
                    <th className="text-center px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden md:table-cell">Juridic</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map((c, i) => (
                    <tr key={c.cui || i} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3">
                        <Link
                          to={`/firma/${c.slug}`}
                          className="text-sm font-medium text-primary hover:underline"
                          data-testid={`company-link-${c.cui}`}
                        >
                          {c.denumire}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground font-mono">{c.cui}</td>
                      <td className="px-4 py-3 text-xs text-muted-foreground hidden md:table-cell">
                        {c.anaf_cod_caen && (
                          <span title={c.caen_description}>{c.anaf_cod_caen}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center hidden sm:table-cell">
                        {c.anaf_stare_startswith_inregistrat ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-700">
                            <CheckCircle className="w-3 h-3" /> Activa
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-red-100 text-red-700">
                            <XCircle className="w-3 h-3" /> Radiata
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-sm hidden lg:table-cell">
                        {c.mf_cifra_afaceri ? `${c.mf_cifra_afaceri.toLocaleString('ro-RO')} RON` : '-'}
                      </td>
                      <td className="px-4 py-3 text-center hidden md:table-cell">
                        {c.has_legal_issues ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-700" title={`${c.dosare_count || 0} dosare`}>
                            <AlertTriangle className="w-3 h-3" /> {c.dosare_count || 0}
                          </span>
                        ) : (
                          <span className="text-xs text-muted-foreground">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6" data-testid="pagination">
                <button
                  onClick={() => handlePage(page - 1)}
                  disabled={page <= 1}
                  className="flex items-center gap-1 px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <ChevronLeft className="w-4 h-4" /> Inapoi
                </button>
                <span className="text-sm text-muted-foreground">
                  Pagina {page} din {totalPages.toLocaleString('ro-RO')}
                </span>
                <button
                  onClick={() => handlePage(page + 1)}
                  disabled={page >= totalPages}
                  className="flex items-center gap-1 px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  Inainte <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default LocalitatePage;
