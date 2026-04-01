import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { MapPin, Building2, ChevronRight } from 'lucide-react';

const JudeteListPage = () => {
  const [judete, setJudete] = useState([]);
  const [loading, setLoading] = useState(true);
  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    const fetchJudete = async () => {
      try {
        const res = await fetch(`${API_URL}/api/locations/judete`);
        if (res.ok) {
          const data = await res.json();
          setJudete(data.judete || []);
        }
      } catch (err) {
        console.error('Failed to load judete:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchJudete();
  }, [API_URL]);

  const totalCompanies = judete.reduce((sum, j) => sum + j.company_count, 0);

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
          <span className="text-foreground font-medium">Judete</span>
        </nav>

        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2" data-testid="judete-title">Firme din Romania pe judete</h1>
          <p className="text-muted-foreground">
            {totalCompanies.toLocaleString('ro-RO')} firme in {judete.length} judete
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3" data-testid="judete-grid">
          {judete.map((judet) => (
            <Link
              key={judet.slug}
              to={`/judet/${judet.slug}`}
              className="group bg-card border border-border rounded-lg p-4 hover:border-primary/50 hover:shadow-md transition-all"
              data-testid={`judet-${judet.slug}`}
            >
              <div className="flex items-start gap-2">
                <MapPin className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                <div className="min-w-0">
                  <div className="font-medium text-sm group-hover:text-primary transition-colors truncate">
                    {judet.name}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {judet.company_count.toLocaleString('ro-RO')} firme
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default JudeteListPage;
