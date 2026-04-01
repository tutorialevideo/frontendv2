import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRight, Search, ChevronLeft, AlertTriangle, CheckCircle, XCircle, MapPin } from 'lucide-react';

const CaenPage = () => {
  const { cod } = useParams();
  const [caenInfo, setCaenInfo] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [topJudete, setTopJudete] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [judetFilter, setJudetFilter] = useState('');
  const PAGE_SIZE = 50;
  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  const makeSlug = (text) => {
    if (!text) return '';
    const diacritics = {'ş':'s','ș':'s','Ş':'S','Ș':'S','ţ':'t','ț':'t','Ţ':'T','Ț':'T','ă':'a','Ă':'A','â':'a','Â':'A','î':'i','Î':'I'};
    let slug = text;
    for (const [k, v] of Object.entries(diacritics)) slug = slug.split(k).join(v);
    return slug.toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/[\s-]+/g, '-').replace(/^-|-$/g, '');
  };

  const loadCompanies = useCallback(async (pageNum = 1, q = '', judet = '') => {
    setLoading(true);
    try {
      const skip = (pageNum - 1) * PAGE_SIZE;
      const params = new URLSearchParams({ skip: String(skip), limit: String(PAGE_SIZE) });
      if (q) params.set('q', q);
      if (judet) params.set('judet', judet);
      const res = await fetch(`${API_URL}/api/caen/code/${cod}?${params}`);
      if (res.ok) {
        const data = await res.json();
        setCompanies(data.companies || []);
        setTotal(data.total || 0);
        setCaenInfo(data.caen || null);
        setTopJudete(data.top_judete || []);
      }
    } catch (err) {
      console.error('Failed to load:', err);
    } finally {
      setLoading(false);
    }
  }, [API_URL, cod]);

  useEffect(() => {
    loadCompanies(1, '', '');
  }, [loadCompanies]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadCompanies(1, search, judetFilter);
  };

  const handleJudetFilter = (j) => {
    const newFilter = judetFilter === j ? '' : j;
    setJudetFilter(newFilter);
    setPage(1);
    loadCompanies(1, search, newFilter);
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handlePage = (p) => {
    setPage(p);
    loadCompanies(p, search, judetFilter);
    window.scrollTo(0, 0);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6 flex-wrap" data-testid="breadcrumb">
          <Link to="/" className="hover:text-primary">Acasa</Link>
          <ChevronRight className="w-3 h-3" />
          <Link to="/caen" className="hover:text-primary">Coduri CAEN</Link>
          <ChevronRight className="w-3 h-3" />
          <span className="text-foreground font-medium">{cod}</span>
        </nav>

        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <span className="px-3 py-1 bg-primary/10 text-primary font-mono font-bold rounded-lg text-lg" data-testid="caen-code">{cod}</span>
            <h1 className="text-2xl font-bold" data-testid="caen-title">{caenInfo?.denumire || `CAEN ${cod}`}</h1>
          </div>
          {caenInfo?.sectiune && (
            <p className="text-sm text-muted-foreground">Sectiunea {caenInfo.sectiune}: {caenInfo.sectiune_denumire}</p>
          )}
          <p className="text-muted-foreground mt-1">{total.toLocaleString('ro-RO')} firme cu acest cod CAEN</p>
        </div>

        {topJudete.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4" data-testid="judet-filters">
            <span className="flex items-center gap-1 text-xs text-muted-foreground py-1.5"><MapPin className="w-3 h-3" /> Judete:</span>
            {topJudete.map(j => (
              <button key={j.judet} onClick={() => handleJudetFilter(j.judet)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${judetFilter === j.judet ? 'bg-primary text-primary-foreground border-primary' : 'border-border hover:bg-muted text-muted-foreground'}`}>
                {j.judet} ({j.count.toLocaleString('ro-RO')})
              </button>
            ))}
          </div>
        )}

        <form onSubmit={handleSearch} className="flex gap-2 mb-6 max-w-lg">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <input type="text" value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Cauta firma dupa denumire sau CUI..."
              className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-background focus:outline-none focus:border-primary text-sm"
              data-testid="company-search" />
          </div>
          <button type="submit" className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:bg-primary/90">Cauta</button>
        </form>

        {loading ? (
          <div className="flex justify-center py-12"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>
        ) : (
          <>
            <div className="bg-card border border-border rounded-xl overflow-hidden" data-testid="companies-table">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase">Denumire</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase">CUI</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden md:table-cell">Locatie</th>
                    <th className="text-center px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden sm:table-cell">Stare</th>
                    <th className="text-right px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden lg:table-cell">Cifra afaceri</th>
                    <th className="text-center px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden md:table-cell">Juridic</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map((c, i) => (
                    <tr key={c.cui || i} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3">
                        <Link to={`/firma/${c.slug}`} className="text-sm font-medium text-primary hover:underline" data-testid={`company-link-${c.cui}`}>{c.denumire}</Link>
                      </td>
                      <td className="px-4 py-3 text-sm text-muted-foreground font-mono">{c.cui}</td>
                      <td className="px-4 py-3 text-xs text-muted-foreground hidden md:table-cell">
                        {c.judet && <Link to={`/judet/${makeSlug(c.judet)}`} className="hover:text-primary">{c.localitate ? `${c.localitate}, ` : ''}{c.judet}</Link>}
                      </td>
                      <td className="px-4 py-3 text-center hidden sm:table-cell">
                        {c.anaf_stare_startswith_inregistrat ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-700"><CheckCircle className="w-3 h-3" /> Activa</span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-red-100 text-red-700"><XCircle className="w-3 h-3" /> Radiata</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-sm hidden lg:table-cell">{c.mf_cifra_afaceri ? `${c.mf_cifra_afaceri.toLocaleString('ro-RO')} RON` : '-'}</td>
                      <td className="px-4 py-3 text-center hidden md:table-cell">
                        {c.has_legal_issues ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-amber-100 text-amber-700"><AlertTriangle className="w-3 h-3" /> {c.dosare_count || 0}</span>
                        ) : <span className="text-xs text-muted-foreground">-</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6" data-testid="pagination">
                <button onClick={() => handlePage(page - 1)} disabled={page <= 1} className="flex items-center gap-1 px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted disabled:opacity-30"><ChevronLeft className="w-4 h-4" /> Inapoi</button>
                <span className="text-sm text-muted-foreground">Pagina {page} din {totalPages.toLocaleString('ro-RO')}</span>
                <button onClick={() => handlePage(page + 1)} disabled={page >= totalPages} className="flex items-center gap-1 px-3 py-2 text-sm border border-border rounded-lg hover:bg-muted disabled:opacity-30">Inainte <ChevronRight className="w-4 h-4" /></button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default CaenPage;
