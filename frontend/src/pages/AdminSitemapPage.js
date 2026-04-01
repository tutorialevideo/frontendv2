import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import AdminLayout from '../components/AdminLayout';
import { Globe, RefreshCw, FileText, MapPin, Briefcase, Building2, ExternalLink, CheckCircle, Clock } from 'lucide-react';

const AdminSitemapPage = () => {
  const navigate = useNavigate();
  const { user, token, isAuthenticated } = useAuth();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  const loadStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/sitemap/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      } else if (res.status === 403) {
        // Not admin - redirect to account
        navigate('/account');
        return;
      }
    } catch (err) {
      console.error('Failed to load status:', err);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token, navigate]);

  useEffect(() => {
    if (token) loadStatus();
  }, [token, loadStatus]);

  // Also load status on mount if token is already available
  useEffect(() => {
    if (token && isAuthenticated) {
      loadStatus();
    }
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API_URL}/api/sitemap/generate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        await loadStatus();
      }
    } catch (err) {
      console.error('Failed to generate:', err);
    } finally {
      setGenerating(false);
    }
  };

  const stats = status?.stats || {};

  const sitemapFiles = [
    {
      name: 'Sitemap Index',
      path: '/api/sitemap/index.xml',
      icon: Globe,
      description: 'Index principal - listeaza toate sub-sitemap-urile',
      count: stats.total_sitemaps || 0,
      countLabel: 'sub-sitemaps'
    },
    {
      name: 'Pagini Statice',
      path: '/api/sitemap/static.xml',
      icon: FileText,
      description: 'Homepage, cautare, judete, CAEN',
      count: 4,
      countLabel: 'pagini'
    },
    {
      name: 'Judete & Localitati',
      path: '/api/sitemap/judete.xml',
      icon: MapPin,
      description: 'Toate judetele si localitatile cu 10+ firme',
      count: (stats.judete || 0) + (stats.localitati || 0),
      countLabel: 'URL-uri'
    },
    {
      name: 'Coduri CAEN',
      path: '/api/sitemap/caen.xml',
      icon: Briefcase,
      description: 'Toate codurile CAEN cu firme active',
      count: stats.caen_codes || 0,
      countLabel: 'URL-uri'
    },
    ...Array.from({ length: stats.company_pages || 0 }, (_, i) => ({
      name: `Firme (pagina ${i + 1})`,
      path: `/api/sitemap/companies-${i + 1}.xml`,
      icon: Building2,
      description: i === 0
        ? `Firme 1 - ${Math.min(stats.urls_per_page || 45000, stats.total_active_companies || 0).toLocaleString('ro-RO')}`
        : `Firme ${(i * (stats.urls_per_page || 45000) + 1).toLocaleString('ro-RO')} - ${Math.min((i + 1) * (stats.urls_per_page || 45000), stats.total_active_companies || 0).toLocaleString('ro-RO')}`,
      count: Math.min(stats.urls_per_page || 45000, Math.max(0, (stats.total_active_companies || 0) - i * (stats.urls_per_page || 45000))),
      countLabel: 'URL-uri'
    }))
  ];

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
    <div className="space-y-6" data-testid="admin-sitemap-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" data-testid="sitemap-title">Generator Sitemap XML</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Genereaza sitemap-uri dinamice pentru Google Search Console
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="flex items-center gap-2 px-5 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 transition-colors"
          data-testid="generate-sitemap-btn"
        >
          {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          {generating ? 'Se actualizeaza...' : 'Actualizeaza Sitemap'}
        </button>
      </div>

      {/* Status card */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="text-xs text-muted-foreground mb-1">Total URL-uri</div>
          <div className="text-2xl font-bold" data-testid="total-urls">
            {(stats.estimated_total_urls || 0).toLocaleString('ro-RO')}
          </div>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="text-xs text-muted-foreground mb-1">Firme active</div>
          <div className="text-2xl font-bold">
            {(stats.total_active_companies || 0).toLocaleString('ro-RO')}
          </div>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="text-xs text-muted-foreground mb-1">Sub-sitemaps</div>
          <div className="text-2xl font-bold">{stats.total_sitemaps || 0}</div>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="text-xs text-muted-foreground mb-1">Ultima generare</div>
          <div className="flex items-center gap-1.5">
            {status?.last_generated ? (
              <>
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm font-medium">
                  {new Date(status.last_generated).toLocaleDateString('ro-RO', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </span>
              </>
            ) : (
              <>
                <Clock className="w-4 h-4 text-amber-500" />
                <span className="text-sm text-muted-foreground">Niciodata</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Sitemap files */}
      <div className="bg-card border border-border rounded-xl overflow-hidden" data-testid="sitemap-files">
        <div className="px-4 py-3 border-b border-border bg-muted/50">
          <h2 className="font-medium text-sm">Fisiere Sitemap</h2>
        </div>
        <div className="divide-y divide-border">
          {sitemapFiles.map((file, i) => (
            <div key={i} className="flex items-center justify-between px-4 py-3 hover:bg-muted/30 transition-colors">
              <div className="flex items-center gap-3">
                <file.icon className="w-4 h-4 text-muted-foreground" />
                <div>
                  <div className="text-sm font-medium">{file.name}</div>
                  <div className="text-xs text-muted-foreground">{file.description}</div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs text-muted-foreground">
                  {file.count.toLocaleString('ro-RO')} {file.countLabel}
                </span>
                <a
                  href={`${API_URL}${file.path}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-primary hover:underline"
                  data-testid={`sitemap-link-${i}`}
                >
                  <ExternalLink className="w-3 h-3" />
                  Deschide
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="font-medium mb-3">Instructiuni Google Search Console</h3>
        <ol className="space-y-2 text-sm text-muted-foreground list-decimal list-inside">
          <li>Deschide <a href="https://search.google.com/search-console" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Google Search Console</a></li>
          <li>Mergi la <strong>Sitemaps</strong> din meniul lateral</li>
          <li>Adauga URL-ul sitemap index: <code className="px-1.5 py-0.5 bg-muted rounded text-xs font-mono">https://mfirme.ro/api/sitemap/index.xml</code></li>
          <li>Google va descoperi automat toate sub-sitemap-urile ({stats.total_sitemaps || 0} fisiere)</li>
          <li>Apasa <strong>"Actualizeaza Sitemap"</strong> de fiecare data cand adaugi date noi</li>
        </ol>
      </div>
    </div>
    </AdminLayout>
  );
};

export default AdminSitemapPage;
