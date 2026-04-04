import React, { useState, useEffect, useCallback } from 'react';
import {
  Database, HardDrive, CheckCircle, XCircle, AlertTriangle,
  RefreshCw, Loader2, Zap, Shield, ChevronDown, ChevronUp, Type
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import AdminLayout from '../components/AdminLayout';

const AdminDbOptimizePage = () => {
  const { token } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState({});
  const [creatingAll, setCreatingAll] = useState(false);
  const [expandedCol, setExpandedCol] = useState(null);
  const [normalizePreview, setNormalizePreview] = useState(null);
  const [normalizeLoading, setNormalizeLoading] = useState(false);
  const [normalizeRunning, setNormalizeRunning] = useState(false);
  const [normalizeResult, setNormalizeResult] = useState(null);
  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  const loadStats = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/db/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to load DB stats:', err);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const createIndex = async (indexName) => {
    setCreating(prev => ({ ...prev, [indexName]: true }));
    try {
      const res = await fetch(`${API_URL}/api/admin/db/create-index`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ index_name: indexName })
      });
      if (res.ok) {
        loadStats();
      }
    } catch (err) {
      console.error('Failed to create index:', err);
    } finally {
      setCreating(prev => ({ ...prev, [indexName]: false }));
    }
  };

  const createAllIndexes = async () => {
    if (!window.confirm('Crezi toate indexurile lipsa? Poate dura cateva minute pe colectii mari.')) return;
    setCreatingAll(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/db/create-all-indexes`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Indexuri create: ${data.created}, deja existente: ${data.already_existed}, erori: ${data.errors}`);
        loadStats();
      }
    } catch (err) {
      console.error('Failed:', err);
    } finally {
      setCreatingAll(false);
    }
  };

  const loadNormalizePreview = async () => {
    setNormalizeLoading(true);
    setNormalizeResult(null);
    try {
      const res = await fetch(`${API_URL}/api/admin/db/normalize-preview`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setNormalizePreview(data);
      }
    } catch (err) {
      console.error('Failed:', err);
    } finally {
      setNormalizeLoading(false);
    }
  };

  const runNormalize = async () => {
    if (!window.confirm(`Normalizezi diacriticele vechi (ş→ș, ţ→ț) pe ${normalizePreview?.total_affected_docs?.toLocaleString('ro-RO')} documente? Operatia este ireversibila.`)) return;
    setNormalizeRunning(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/db/normalize-diacritics`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }
      });
      if (res.ok) {
        const data = await res.json();
        setNormalizeResult(data);
        setNormalizePreview(null);
        loadStats();
      }
    } catch (err) {
      console.error('Failed:', err);
    } finally {
      setNormalizeRunning(false);
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </AdminLayout>
    );
  }

  const missingIndexes = stats?.recommendations?.filter(r => !r.exists) || [];
  const existingRecs = stats?.recommendations?.filter(r => r.exists) || [];

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold" data-testid="db-optimize-title">Optimizare Baza de Date</h2>
            <p className="text-muted-foreground">Statistici, indexuri si recomandari de performanta</p>
          </div>
          <button onClick={loadStats} className="flex items-center gap-2 px-4 py-2 bg-secondary rounded-lg hover:bg-secondary/80">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
        </div>

        {/* Health Score */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-card border border-border rounded-xl p-5" data-testid="health-score-card">
            <div className="flex items-center gap-3 mb-2">
              <Shield className={`w-6 h-6 ${stats?.health_score >= 80 ? 'text-green-500' : stats?.health_score >= 50 ? 'text-amber-500' : 'text-red-500'}`} />
              <span className="text-sm text-muted-foreground">Scor Sanatate</span>
            </div>
            <p className={`text-3xl font-bold ${stats?.health_score >= 80 ? 'text-green-600' : stats?.health_score >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
              {stats?.health_score || 0}%
            </p>
          </div>
          <div className="bg-card border border-border rounded-xl p-5">
            <div className="flex items-center gap-3 mb-2">
              <HardDrive className="w-6 h-6 text-blue-500" />
              <span className="text-sm text-muted-foreground">Date Totale</span>
            </div>
            <p className="text-3xl font-bold">{stats?.total_data_size_mb || 0} <span className="text-base font-normal text-muted-foreground">MB</span></p>
          </div>
          <div className="bg-card border border-border rounded-xl p-5">
            <div className="flex items-center gap-3 mb-2">
              <Database className="w-6 h-6 text-purple-500" />
              <span className="text-sm text-muted-foreground">Indexuri</span>
            </div>
            <p className="text-3xl font-bold">{stats?.total_index_size_mb || 0} <span className="text-base font-normal text-muted-foreground">MB</span></p>
          </div>
          <div className="bg-card border border-border rounded-xl p-5">
            <div className="flex items-center gap-3 mb-2">
              {missingIndexes.length > 0 ? (
                <AlertTriangle className="w-6 h-6 text-amber-500" />
              ) : (
                <CheckCircle className="w-6 h-6 text-green-500" />
              )}
              <span className="text-sm text-muted-foreground">Indexuri Lipsa</span>
            </div>
            <p className={`text-3xl font-bold ${missingIndexes.length > 0 ? 'text-amber-600' : 'text-green-600'}`}>
              {missingIndexes.length} <span className="text-base font-normal text-muted-foreground">/ {stats?.total_recommended || 0}</span>
            </p>
          </div>
        </div>

        {/* Missing Indexes */}
        {missingIndexes.length > 0 && (
          <div className="bg-card border border-amber-200 rounded-xl p-6" data-testid="missing-indexes">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-amber-500" />
                Indexuri Recomandate Lipsa ({missingIndexes.length})
              </h3>
              <button
                onClick={createAllIndexes}
                disabled={creatingAll}
                className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
                data-testid="create-all-indexes-btn"
              >
                {creatingAll ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                Creeaza Toate Indexurile
              </button>
            </div>

            <div className="space-y-3">
              {missingIndexes.map((rec) => (
                <div key={`${rec.collection}.${rec.name}`} className="flex items-center justify-between p-3 bg-amber-50 border border-amber-100 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-medium text-amber-800">{rec.collection}.{rec.name}</span>
                      {rec.priority === 'critical' && (
                        <span className="px-1.5 py-0.5 text-[10px] font-bold bg-red-100 text-red-700 rounded">CRITIC</span>
                      )}
                    </div>
                    <p className="text-xs text-amber-600 mt-0.5">{rec.reason}</p>
                    <p className="text-xs text-muted-foreground font-mono mt-0.5">{rec.keys}</p>
                  </div>
                  <button
                    onClick={() => createIndex(rec.name)}
                    disabled={creating[rec.name]}
                    className="flex items-center gap-1 px-3 py-1.5 bg-amber-600 text-white rounded-lg text-xs hover:bg-amber-700 disabled:opacity-50 shrink-0 ml-3"
                    data-testid={`create-index-${rec.name}`}
                  >
                    {creating[rec.name] ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                    Creeaza
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Existing Recommended Indexes */}
        {existingRecs.length > 0 && (
          <div className="bg-card border border-green-200 rounded-xl p-6" data-testid="existing-indexes">
            <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
              <CheckCircle className="w-5 h-5 text-green-500" />
              Indexuri Active ({existingRecs.length})
            </h3>
            <div className="space-y-2">
              {existingRecs.map((rec) => (
                <div key={`${rec.collection}.${rec.name}`} className="flex items-center gap-3 p-3 bg-green-50 border border-green-100 rounded-lg">
                  <CheckCircle className="w-4 h-4 text-green-500 shrink-0" />
                  <div className="flex-1">
                    <span className="font-mono text-sm font-medium text-green-800">{rec.collection}.{rec.name}</span>
                    <p className="text-xs text-green-600">{rec.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Diacritics Normalization */}
        <div className="bg-card border border-border rounded-xl p-6" data-testid="normalize-section">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Type className="w-5 h-5 text-blue-500" />
                Normalizare Diacritice
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                Converteste diacriticele vechi romanesti (ş→ș, ţ→ț) la formatul standard. Rezolva duplicatele de judete/localitati.
              </p>
            </div>
            <button
              onClick={loadNormalizePreview}
              disabled={normalizeLoading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 shrink-0"
              data-testid="normalize-preview-btn"
            >
              {normalizeLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Scaneaza
            </button>
          </div>

          {normalizePreview && normalizePreview.total_changes > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <span className="text-sm font-medium text-blue-800">
                  {normalizePreview.total_changes} valori de corectat in {normalizePreview.total_affected_docs.toLocaleString('ro-RO')} documente
                </span>
                <button
                  onClick={runNormalize}
                  disabled={normalizeRunning}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  data-testid="normalize-run-btn"
                >
                  {normalizeRunning ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
                  Normalizeaza Acum
                </button>
              </div>
              <div className="max-h-60 overflow-y-auto space-y-1">
                {normalizePreview.changes.map((c, i) => (
                  <div key={i} className="flex items-center gap-3 px-3 py-2 bg-secondary/50 rounded text-xs">
                    <span className="px-1.5 py-0.5 bg-muted rounded font-mono text-muted-foreground">{c.field}</span>
                    <span className="text-red-600 line-through font-mono">{c.old_value}</span>
                    <span className="text-muted-foreground">→</span>
                    <span className="text-green-600 font-mono font-medium">{c.new_value}</span>
                    <span className="ml-auto text-muted-foreground">{c.affected_docs.toLocaleString('ro-RO')} docs</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {normalizePreview && normalizePreview.total_changes === 0 && (
            <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-sm text-green-700">Toate diacriticele sunt deja normalizate. Nimic de corectat.</span>
            </div>
          )}

          {normalizeResult && (
            <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="font-medium text-green-800">
                  Normalizare completa: {normalizeResult.total_modified.toLocaleString('ro-RO')} documente actualizate
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Collection Details */}
        <div className="bg-card border border-border rounded-xl p-6" data-testid="collection-details">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Database className="w-5 h-5" />
            Detalii Colectii
          </h3>

          <div className="space-y-2">
            {stats?.collections?.map((col) => (
              <div key={col.name} className="border border-border rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpandedCol(expandedCol === col.name ? null : col.name)}
                  className="w-full flex items-center justify-between p-4 hover:bg-muted/30 transition-colors text-left"
                  data-testid={`collection-${col.name}`}
                >
                  <div className="flex items-center gap-3">
                    <Database className="w-4 h-4 text-muted-foreground" />
                    <span className="font-medium capitalize">{col.name}</span>
                    <span className="text-sm text-muted-foreground">({col.count.toLocaleString('ro-RO')} docs)</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-muted-foreground">{col.data_size_mb} MB</span>
                    <span className="text-xs px-2 py-0.5 bg-secondary rounded">{col.index_count} idx</span>
                    {expandedCol === col.name ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </button>
                {expandedCol === col.name && (
                  <div className="px-4 pb-4 border-t border-border pt-3">
                    <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
                      <div>
                        <span className="text-muted-foreground">Documente:</span>
                        <span className="ml-2 font-mono">{col.count.toLocaleString('ro-RO')}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Date:</span>
                        <span className="ml-2 font-mono">{col.data_size_mb} MB</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Indexuri:</span>
                        <span className="ml-2 font-mono">{col.index_size_mb} MB</span>
                      </div>
                    </div>
                    {col.indexes.length > 0 ? (
                      <div className="space-y-1">
                        {col.indexes.map((idx) => (
                          <div key={idx.name} className="flex items-center gap-2 px-3 py-2 bg-secondary/50 rounded text-xs font-mono">
                            <span className="text-primary font-medium">{idx.name}</span>
                            <span className="text-muted-foreground">{idx.keys}</span>
                            {idx.unique && <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]">UNIC</span>}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">Fara indexuri custom (doar _id)</p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminDbOptimizePage;
