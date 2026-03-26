import React, { useState, useEffect, useCallback } from 'react';
import { 
  Database, 
  Cloud, 
  HardDrive, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle,
  Clock,
  Server,
  Loader2,
  ToggleLeft,
  ToggleRight,
  ArrowDownToLine
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

const AdminSyncPage = () => {
  const { token } = useAuth();
  const [syncStatus, setSyncStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  const fetchSyncStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/sync/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (res.ok) {
        const data = await res.json();
        setSyncStatus(data);
        setError(null);
      } else {
        setError('Failed to fetch sync status');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [token, API_URL]);

  useEffect(() => {
    fetchSyncStatus();
    
    // Auto-refresh every 5 seconds when syncing
    const interval = setInterval(() => {
      if (syncing) {
        fetchSyncStatus();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [fetchSyncStatus, syncing]);

  const triggerFullSync = async () => {
    if (!window.confirm('Aceasta va sincroniza toate colecțiile (~1.2M firme). Poate dura 10-30 minute. Continui?')) {
      return;
    }

    setSyncing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/sync/trigger-full`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        // Start polling for status
        const pollInterval = setInterval(async () => {
          await fetchSyncStatus();
        }, 3000);

        // Stop polling after 30 minutes max
        setTimeout(() => {
          clearInterval(pollInterval);
          setSyncing(false);
        }, 30 * 60 * 1000);
      } else {
        const data = await res.json();
        alert(data.detail || 'Sync failed to start');
        setSyncing(false);
      }
    } catch (err) {
      alert('Error: ' + err.message);
      setSyncing(false);
    }
  };

  const triggerCollectionSync = async (collection) => {
    setSyncing(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/sync/trigger-collection/${collection}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        fetchSyncStatus();
      } else {
        const data = await res.json();
        alert(data.detail || 'Sync failed');
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  const switchDatabaseMode = async (useLocal) => {
    try {
      const res = await fetch(`${API_URL}/api/admin/sync/switch-mode?use_local=${useLocal}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        fetchSyncStatus();
      } else {
        const data = await res.json();
        alert(data.message || 'Switch failed');
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  const formatNumber = (num) => {
    return num?.toLocaleString('ro-RO') || '0';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString('ro-RO');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const isUsingLocal = syncStatus?.mode === 'local';
  const localDb = syncStatus?.local_db || {};
  const cloudCounts = syncStatus?.cloud_counts || {};
  const syncService = syncStatus?.sync_service || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Sincronizare Bază de Date</h2>
          <p className="text-muted-foreground">
            Gestionează sincronizarea între MongoDB Cloud și Local
          </p>
        </div>
        <button
          onClick={fetchSyncStatus}
          className="flex items-center gap-2 px-4 py-2 bg-secondary text-foreground rounded-lg hover:bg-secondary/80"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-600">
          {error}
        </div>
      )}

      {/* Database Mode Toggle */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`p-3 rounded-xl ${isUsingLocal ? 'bg-green-500/10' : 'bg-blue-500/10'}`}>
              {isUsingLocal ? (
                <HardDrive className="w-8 h-8 text-green-600" />
              ) : (
                <Cloud className="w-8 h-8 text-blue-600" />
              )}
            </div>
            <div>
              <h3 className="text-lg font-semibold">
                Mod curent: {isUsingLocal ? 'LOCAL' : 'CLOUD'}
              </h3>
              <p className="text-sm text-muted-foreground">
                {isUsingLocal 
                  ? 'Citirile se fac din MongoDB local (rapid)' 
                  : 'Citirile se fac din MongoDB Atlas (cloud)'}
              </p>
            </div>
          </div>
          
          <button
            onClick={() => switchDatabaseMode(!isUsingLocal)}
            disabled={!localDb.available && !isUsingLocal}
            className="flex items-center gap-2"
          >
            {isUsingLocal ? (
              <ToggleRight className="w-12 h-12 text-green-500" />
            ) : (
              <ToggleLeft className="w-12 h-12 text-muted-foreground" />
            )}
          </button>
        </div>

        {!localDb.available && (
          <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-700 text-sm">
            <AlertCircle className="w-4 h-4 inline mr-2" />
            Baza de date locală nu este disponibilă sau nu are date. Rulează un sync complet mai întâi.
          </div>
        )}
      </div>

      {/* Sync Status Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Cloud Database */}
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <Cloud className="w-6 h-6 text-blue-500" />
            <h3 className="text-lg font-semibold">MongoDB Cloud (Atlas)</h3>
          </div>
          
          <div className="space-y-3">
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Firme</span>
              <span className="font-mono font-medium">{formatNumber(cloudCounts.firme)}</span>
            </div>
            <div className="flex justify-between py-2 border-b border-border">
              <span className="text-muted-foreground">Bilanțuri</span>
              <span className="font-mono font-medium">{formatNumber(cloudCounts.bilanturi)}</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-muted-foreground">Status</span>
              <span className="flex items-center gap-1 text-green-600">
                <CheckCircle className="w-4 h-4" />
                Connected
              </span>
            </div>
          </div>
        </div>

        {/* Local Database */}
        <div className="bg-card border border-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <HardDrive className="w-6 h-6 text-green-500" />
            <h3 className="text-lg font-semibold">MongoDB Local</h3>
          </div>
          
          {localDb.available ? (
            <div className="space-y-3">
              {Object.entries(localDb.collections || {}).map(([name, count]) => (
                <div key={name} className="flex justify-between py-2 border-b border-border">
                  <span className="text-muted-foreground capitalize">{name}</span>
                  <span className="font-mono font-medium">{formatNumber(count)}</span>
                </div>
              ))}
              <div className="flex justify-between py-2">
                <span className="text-muted-foreground">Status</span>
                <span className={`flex items-center gap-1 ${isUsingLocal ? 'text-green-600' : 'text-amber-600'}`}>
                  {isUsingLocal ? (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Active
                    </>
                  ) : (
                    <>
                      <Clock className="w-4 h-4" />
                      Standby
                    </>
                  )}
                </span>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Database className="w-12 h-12 mx-auto mb-3 opacity-30" />
              <p>Nu există date locale</p>
              <p className="text-sm">Rulează un sync complet</p>
            </div>
          )}
        </div>
      </div>

      {/* Sync Controls */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <ArrowDownToLine className="w-5 h-5" />
          Sincronizare
        </h3>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={triggerFullSync}
            disabled={syncing}
            className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
          >
            {syncing ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <RefreshCw className="w-5 h-5" />
            )}
            Sync Complet (toate colecțiile)
          </button>

          <button
            onClick={() => triggerCollectionSync('firme')}
            disabled={syncing}
            className="px-4 py-3 bg-secondary text-foreground rounded-lg hover:bg-secondary/80 disabled:opacity-50"
          >
            Sync Firme
          </button>

          <button
            onClick={() => triggerCollectionSync('bilanturi')}
            disabled={syncing}
            className="px-4 py-3 bg-secondary text-foreground rounded-lg hover:bg-secondary/80 disabled:opacity-50"
          >
            Sync Bilanțuri
          </button>
        </div>

        {syncing && (
          <div className="mt-4 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              <div>
                <p className="font-medium text-blue-800">Sincronizare în curs...</p>
                <p className="text-sm text-blue-600">
                  Aceasta poate dura câteva minute. Pagina se actualizează automat.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sync Service Status */}
      <div className="bg-card border border-border rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Server className="w-5 h-5" />
          Sync Service Status
        </h3>

        {syncService.error ? (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-600">
            <AlertCircle className="w-4 h-4 inline mr-2" />
            Sync service indisponibil: {syncService.error}
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 bg-secondary/50 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Status</p>
              <p className="font-medium capitalize">{syncService.status || 'Unknown'}</p>
            </div>
            <div className="p-4 bg-secondary/50 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Running</p>
              <p className="font-medium">{syncService.is_running ? 'Da' : 'Nu'}</p>
            </div>
            <div className="p-4 bg-secondary/50 rounded-lg">
              <p className="text-sm text-muted-foreground mb-1">Last Check</p>
              <p className="font-medium">{formatDate(syncService.last_check)}</p>
            </div>
          </div>
        )}

        {/* Collection sync status */}
        {syncService.collections && Object.keys(syncService.collections).length > 0 && (
          <div className="mt-4">
            <h4 className="text-sm font-medium text-muted-foreground mb-2">Colecții sincronizate:</h4>
            <div className="space-y-2">
              {Object.entries(syncService.collections).map(([name, info]) => (
                <div key={name} className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                  <span className="font-medium capitalize">{name}</span>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-muted-foreground">
                      {formatNumber(info.documents_count || 0)} docs
                    </span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      info.status === 'synced' ? 'bg-green-500/10 text-green-600' :
                      info.status === 'syncing' ? 'bg-blue-500/10 text-blue-600' :
                      info.status === 'error' ? 'bg-red-500/10 text-red-600' :
                      'bg-gray-500/10 text-gray-600'
                    }`}>
                      {info.status || 'unknown'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminSyncPage;
