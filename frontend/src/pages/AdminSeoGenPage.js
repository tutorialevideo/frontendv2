import React, { useState, useEffect, useCallback } from 'react';
import { Sparkles, Play, Square, RefreshCw, Loader2, Eye, Zap, AlertTriangle, CheckCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import AdminLayout from '../components/AdminLayout';

const AdminSeoGenPage = () => {
  const { token } = useAuth();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [concurrency, setConcurrency] = useState(5);
  const [limit, setLimit] = useState(0);
  const [previewCui, setPreviewCui] = useState('');
  const [preview, setPreview] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/seo-gen/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Status fetch failed:', err);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const startGen = async () => {
    setStarting(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/seo-gen/start`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ concurrency, limit: limit || 0 })
      });
      if (res.ok) fetchStatus();
    } catch (err) { console.error(err); }
    finally { setStarting(false); }
  };

  const stopGen = async () => {
    try {
      await fetch(`${API_URL}/api/admin/seo-gen/stop`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchStatus();
    } catch (err) { console.error(err); }
  };

  const runPreview = async () => {
    if (!previewCui) return;
    setPreviewLoading(true);
    setPreview(null);
    try {
      const res = await fetch(`${API_URL}/api/admin/seo-gen/preview/${previewCui}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setPreview(await res.json());
      } else {
        setPreview({ error: 'Firma nu a fost găsită' });
      }
    } catch (err) {
      setPreview({ error: err.message });
    } finally {
      setPreviewLoading(false);
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </AdminLayout>
    );
  }

  const isRunning = status?.running;
  const pct = status?.total_target > 0
    ? Math.round(((status.processed + status.errors + status.skipped) / status.total_target) * 100)
    : 0;

  const eta = status?.speed_per_min > 0 && status?.remaining > 0
    ? Math.round(status.remaining / status.speed_per_min)
    : null;

  return (
    <AdminLayout>
      <div className="space-y-6 max-w-5xl" data-testid="seo-gen-page">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-amber-500" />
            Generare Texte SEO
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Generare automată descrieri SEO cu Gemini Flash pentru firmele active.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-xs text-muted-foreground">Firme active</div>
            <div className="text-xl font-bold mt-1" data-testid="total-active">
              {status?.total_active?.toLocaleString('ro-RO') || '—'}
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-xs text-muted-foreground">Cu descriere SEO</div>
            <div className="text-xl font-bold mt-1 text-green-600" data-testid="total-with-seo">
              {status?.total_with_seo?.toLocaleString('ro-RO') || '0'}
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-xs text-muted-foreground">Rămase</div>
            <div className="text-xl font-bold mt-1 text-amber-600" data-testid="remaining">
              {status?.remaining?.toLocaleString('ro-RO') || '—'}
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="text-xs text-muted-foreground">Viteză</div>
            <div className="text-xl font-bold mt-1" data-testid="speed">
              {isRunning ? `${status?.speed_per_min || 0}/min` : '—'}
            </div>
          </div>
        </div>

        {/* Control Panel */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4">Control Generare</h3>

          {!isRunning ? (
            <div className="space-y-4">
              <div className="flex items-end gap-4">
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">Paralelism (1-10)</label>
                  <input
                    type="number" min={1} max={10} value={concurrency}
                    onChange={e => setConcurrency(Math.max(1, Math.min(10, parseInt(e.target.value) || 1)))}
                    className="w-24 px-3 py-2 bg-secondary border border-border rounded-lg text-sm"
                    data-testid="concurrency-input"
                  />
                </div>
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">Limită (0 = toate)</label>
                  <input
                    type="number" min={0} value={limit}
                    onChange={e => setLimit(Math.max(0, parseInt(e.target.value) || 0))}
                    className="w-32 px-3 py-2 bg-secondary border border-border rounded-lg text-sm"
                    data-testid="limit-input"
                  />
                </div>
                <button
                  onClick={startGen}
                  disabled={starting}
                  className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  data-testid="start-btn"
                >
                  {starting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                  Pornește Generarea
                </button>
              </div>
              <p className="text-xs text-muted-foreground">
                Firmele sunt procesate în ordinea cifrei de afaceri (cele mai mari primele). Procesul poate fi oprit oricând.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Progress Bar */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-muted-foreground">Progres</span>
                  <span className="font-medium">{pct}%</span>
                </div>
                <div className="w-full h-3 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all duration-500"
                    style={{ width: `${pct}%` }}
                    data-testid="progress-bar"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                <div className="bg-green-50 border border-green-200 rounded-lg p-2 text-center">
                  <div className="text-green-700 font-bold">{status.processed}</div>
                  <div className="text-[10px] text-green-600">Procesate</div>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-lg p-2 text-center">
                  <div className="text-red-700 font-bold">{status.errors}</div>
                  <div className="text-[10px] text-red-600">Erori</div>
                </div>
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-2 text-center">
                  <div className="text-amber-700 font-bold">{status.skipped}</div>
                  <div className="text-[10px] text-amber-600">Sărite</div>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-2 text-center">
                  <div className="text-blue-700 font-bold">{status.total_target?.toLocaleString('ro-RO')}</div>
                  <div className="text-[10px] text-blue-600">Total țintă</div>
                </div>
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-2 text-center">
                  <div className="text-purple-700 font-bold">
                    {eta ? `~${eta} min` : '—'}
                  </div>
                  <div className="text-[10px] text-purple-600">ETA</div>
                </div>
              </div>

              {status.last_error && (
                <div className="flex items-start gap-2 p-2 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
                  <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0" />
                  <span className="break-all">{status.last_error}</span>
                </div>
              )}

              <button
                onClick={stopGen}
                className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                data-testid="stop-btn"
              >
                <Square className="w-4 h-4" /> Oprește
              </button>
            </div>
          )}
        </div>

        {/* Preview */}
        <div className="bg-card border border-border rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Eye className="w-5 h-5 text-blue-500" />
            Preview — Generare pentru o firmă
          </h3>
          <div className="flex items-end gap-3 mb-4">
            <div className="flex-1 max-w-xs">
              <label className="block text-xs text-muted-foreground mb-1">CUI firmă</label>
              <input
                type="text"
                value={previewCui}
                onChange={e => setPreviewCui(e.target.value)}
                placeholder="ex: 2113693"
                className="w-full px-3 py-2 bg-secondary border border-border rounded-lg text-sm"
                data-testid="preview-cui-input"
                onKeyDown={e => e.key === 'Enter' && runPreview()}
              />
            </div>
            <button
              onClick={runPreview}
              disabled={previewLoading || !previewCui}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              data-testid="preview-btn"
            >
              {previewLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              Generează
            </button>
          </div>

          {preview && !preview.error && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg" data-testid="preview-result">
              <div className="text-xs text-green-600 font-medium mb-1">
                {preview.denumire} (CUI: {preview.cui})
              </div>
              <p className="text-sm text-green-900 leading-relaxed">{preview.seo_description}</p>
            </div>
          )}

          {preview?.error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {preview.error}
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminSeoGenPage;
