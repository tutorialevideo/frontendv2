import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { MapPin, Building2, ChevronRight, Search } from 'lucide-react';

const JudetPage = () => {
  const { judetSlug } = useParams();
  const [localities, setLocalities] = useState([]);
  const [judetName, setJudetName] = useState('');
  const [totalCompanies, setTotalCompanies] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
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

        {/* Search */}
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
      </div>
    </div>
  );
};

export default JudetPage;
