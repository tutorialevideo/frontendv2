import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight, Search, Briefcase } from 'lucide-react';

const CaenListPage = () => {
  const [codes, setCodes] = useState([]);
  const [sections, setSections] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeSection, setActiveSection] = useState('');
  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    const fetchSections = async () => {
      try {
        const res = await fetch(`${API_URL}/api/caen/sections`);
        if (res.ok) {
          const data = await res.json();
          setSections(data.sections || []);
        }
      } catch (err) {
        console.error('Failed to load sections:', err);
      }
    };
    fetchSections();
  }, [API_URL]);

  useEffect(() => {
    const fetchCodes = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (activeSection) params.set('sectiune', activeSection);
        if (search) params.set('q', search);
        const res = await fetch(`${API_URL}/api/caen/codes?${params}`);
        if (res.ok) {
          const data = await res.json();
          setCodes(data.codes || []);
        }
      } catch (err) {
        console.error('Failed to load CAEN codes:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchCodes();
  }, [API_URL, activeSection, search]);

  const totalCompanies = codes.reduce((sum, c) => sum + c.company_count, 0);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <nav className="flex items-center gap-2 text-sm text-muted-foreground mb-6" data-testid="breadcrumb">
          <Link to="/" className="hover:text-primary">Acasa</Link>
          <ChevronRight className="w-3 h-3" />
          <span className="text-foreground font-medium">Coduri CAEN</span>
        </nav>

        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2" data-testid="caen-title">Coduri CAEN - Activitati economice</h1>
          <p className="text-muted-foreground">
            {codes.length} coduri CAEN, {totalCompanies.toLocaleString('ro-RO')} firme
          </p>
        </div>

        {/* Search */}
        <div className="relative mb-4 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Cauta cod CAEN sau activitate..."
            className="w-full pl-10 pr-4 py-2 border border-border rounded-lg bg-background focus:outline-none focus:border-primary text-sm"
            data-testid="caen-search"
          />
        </div>

        {/* Section filters */}
        <div className="flex flex-wrap gap-2 mb-6" data-testid="section-filters">
          <button
            onClick={() => setActiveSection('')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${!activeSection ? 'bg-primary text-primary-foreground border-primary' : 'border-border hover:bg-muted text-muted-foreground'}`}
          >
            Toate
          </button>
          {sections.map(s => (
            <button
              key={s.sectiune}
              onClick={() => setActiveSection(s.sectiune)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${activeSection === s.sectiune ? 'bg-primary text-primary-foreground border-primary' : 'border-border hover:bg-muted text-muted-foreground'}`}
              title={s.denumire}
            >
              {s.sectiune}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <div className="bg-card border border-border rounded-xl overflow-hidden" data-testid="caen-table">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase w-20">Cod</th>
                  <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase">Activitate</th>
                  <th className="text-center px-4 py-3 text-xs font-medium text-muted-foreground uppercase hidden sm:table-cell w-16">Sect.</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-muted-foreground uppercase w-28">Firme</th>
                </tr>
              </thead>
              <tbody>
                {codes.map((c) => (
                  <tr key={c.cod} className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-3">
                      <Link
                        to={`/caen/${c.cod}`}
                        className="text-sm font-mono font-semibold text-primary hover:underline"
                        data-testid={`caen-link-${c.cod}`}
                      >
                        {c.cod}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <Link to={`/caen/${c.cod}`} className="hover:text-primary transition-colors">
                        {c.denumire || '-'}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-center hidden sm:table-cell">
                      {c.sectiune && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-muted" title={c.sectiune_denumire}>
                          {c.sectiune}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-sm font-medium">
                      {c.company_count.toLocaleString('ro-RO')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default CaenListPage;
