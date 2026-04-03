import React, { useState, useEffect, useCallback } from 'react';
import { Helmet } from 'react-helmet-async';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import AdminLayout from '../components/AdminLayout';
import { 
  Search, Database, RefreshCw, Play, Square, Trash2, 
  CheckCircle, XCircle, AlertCircle, Clock, HardDrive,
  FileText, Terminal, Copy, Check, Zap, Server
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const AdminElasticsearchPage = () => {
  const navigate = useNavigate();
  const { user, token, isAuthenticated, loading: authLoading } = useAuth();
  
  const [status, setStatus] = useState(null);
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  
  // Test search state
  const [testQuery, setTestQuery] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [searching, setSearching] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/elasticsearch/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch ES status:', error);
    }
  }, [token]);

  const fetchConfig = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/elasticsearch/config`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Failed to fetch config:', error);
    }
  }, [token]);

  useEffect(() => {
    if (authLoading) return;
    
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    if (user?.role !== 'admin') {
      navigate('/');
      return;
    }
    
    const loadData = async () => {
      await Promise.all([fetchStatus(), fetchConfig()]);
      setLoading(false);
    };
    loadData();
  }, [isAuthenticated, user, navigate, authLoading, fetchStatus, fetchConfig]);

  // Auto-refresh status during indexing
  useEffect(() => {
    if (status?.indexing?.is_running) {
      const interval = setInterval(fetchStatus, 3000);
      return () => clearInterval(interval);
    }
  }, [status?.indexing?.is_running, fetchStatus]);

  const createIndex = async () => {
    setActionLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/elasticsearch/create-index`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        alert('Index creat cu succes!');
        fetchStatus();
      } else {
        alert('Eroare: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      alert('Eroare la creare index: ' + error.message);
    } finally {
      setActionLoading(false);
    }
  };

  const startIndexing = async () => {
    setActionLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/elasticsearch/start-indexing`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        alert('Indexarea a început!');
        fetchStatus();
      } else {
        alert('Eroare: ' + (data.detail || data.error || 'Unknown error'));
      }
    } catch (error) {
      alert('Eroare la pornire indexare: ' + error.message);
    } finally {
      setActionLoading(false);
    }
  };

  const stopIndexing = async () => {
    try {
      await fetch(`${API_URL}/api/elasticsearch/stop-indexing`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchStatus();
    } catch (error) {
      console.error('Failed to stop indexing:', error);
    }
  };

  const deleteIndex = async () => {
    if (!window.confirm('Sigur vrei să ștergi indexul? Toate datele indexate vor fi pierdute.')) {
      return;
    }
    
    setActionLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/elasticsearch/delete-index`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.success) {
        alert('Index șters!');
        fetchStatus();
      }
    } catch (error) {
      alert('Eroare: ' + error.message);
    } finally {
      setActionLoading(false);
    }
  };

  const testSearch = async () => {
    if (!testQuery.trim()) return;
    
    setSearching(true);
    try {
      const res = await fetch(`${API_URL}/api/elasticsearch/search/simple?q=${encodeURIComponent(testQuery)}&limit=5`);
      if (res.ok) {
        const data = await res.json();
        setTestResults(data);
      } else {
        const error = await res.json();
        setTestResults({ error: error.detail || 'Search failed' });
      }
    } catch (error) {
      setTestResults({ error: error.message });
    } finally {
      setSearching(false);
    }
  };

  const copyCommands = () => {
    if (config?.setup_commands) {
      navigator.clipboard.writeText(config.setup_commands.join('\n'));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (loading || authLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </AdminLayout>
    );
  }

  const isConnected = status?.connected;
  const indexExists = status?.index?.exists;
  const isIndexing = status?.indexing?.is_running;

  return (
    <AdminLayout>
      <Helmet>
        <title>Elasticsearch | Admin RapoarteFirme</title>
      </Helmet>

      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold flex items-center gap-3">
              <Search className="w-7 h-7 text-amber-500" />
              Elasticsearch
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Motor de căutare fuzzy pentru 1.2M+ firme
            </p>
          </div>
          <button
            onClick={fetchStatus}
            className="mt-4 sm:mt-0 inline-flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Reîncarcă status
          </button>
        </div>

        {/* Connection Status */}
        <div className={`rounded-xl p-6 border ${isConnected ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <div className="flex items-center gap-4">
            {isConnected ? (
              <CheckCircle className="w-10 h-10 text-green-500" />
            ) : (
              <XCircle className="w-10 h-10 text-red-500" />
            )}
            <div>
              <h2 className={`text-lg font-semibold ${isConnected ? 'text-green-800' : 'text-red-800'}`}>
                {isConnected ? 'Elasticsearch Conectat' : 'Elasticsearch Neconectat'}
              </h2>
              <p className={`text-sm ${isConnected ? 'text-green-700' : 'text-red-700'}`}>
                {isConnected 
                  ? `Cluster: ${status.cluster?.cluster_name} | Status: ${status.cluster?.status}`
                  : 'Urmează pașii de mai jos pentru a porni Elasticsearch'
                }
              </p>
            </div>
          </div>
        </div>

        {/* Setup Instructions (if not connected) */}
        {!isConnected && config && (
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Terminal className="w-5 h-5" />
              Setup Elasticsearch cu Docker
            </h3>
            
            <div className="bg-gray-900 rounded-lg p-4 font-mono text-sm text-gray-100 relative">
              <button
                onClick={copyCommands}
                className="absolute top-2 right-2 p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4 text-gray-400" />}
              </button>
              <pre className="whitespace-pre-wrap">
{`# Navighează la directorul docker
cd /app/docker

# Fă script-ul executabil
chmod +x setup-elasticsearch.sh

# Rulează setup-ul
./setup-elasticsearch.sh`}
              </pre>
            </div>
            
            <div className="mt-4 text-sm text-muted-foreground">
              <p><strong>Cerințe:</strong> Docker și Docker Compose instalate pe server.</p>
              <p className="mt-1"><strong>Resurse:</strong> Minim 2GB RAM pentru Elasticsearch.</p>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        {isConnected && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Database className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-semibold">
                    {indexExists ? status.index.docs_count.toLocaleString() : 0}
                  </div>
                  <div className="text-xs text-muted-foreground">Documente indexate</div>
                </div>
              </div>
            </div>
            
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <HardDrive className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-semibold">
                    {indexExists ? status.index.size_human : '0 MB'}
                  </div>
                  <div className="text-xs text-muted-foreground">Dimensiune index</div>
                </div>
              </div>
            </div>
            
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                  <Server className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <div className="text-2xl font-semibold capitalize">
                    {status.cluster?.status || 'N/A'}
                  </div>
                  <div className="text-xs text-muted-foreground">Cluster status</div>
                </div>
              </div>
            </div>
            
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${indexExists ? 'bg-green-100' : 'bg-gray-100'}`}>
                  <FileText className={`w-5 h-5 ${indexExists ? 'text-green-600' : 'text-gray-400'}`} />
                </div>
                <div>
                  <div className="text-2xl font-semibold">
                    {indexExists ? 'Da' : 'Nu'}
                  </div>
                  <div className="text-xs text-muted-foreground">Index există</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Indexing Progress */}
        {isIndexing && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-blue-800 flex items-center gap-2">
                <Clock className="w-5 h-5 animate-spin" />
                Indexare în curs...
              </h3>
              <button
                onClick={stopIndexing}
                className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm font-medium"
              >
                Oprește
              </button>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-blue-700">
                <span>{status.indexing.indexed.toLocaleString()} / {status.indexing.total.toLocaleString()} firme</span>
                <span>{status.indexing.progress_percent}%</span>
              </div>
              <div className="h-3 bg-blue-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-500 rounded-full transition-all duration-500"
                  style={{ width: `${status.indexing.progress_percent}%` }}
                />
              </div>
              {status.indexing.started_at && (
                <p className="text-xs text-blue-600">
                  Început la: {new Date(status.indexing.started_at).toLocaleString('ro-RO')}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Actions */}
        {isConnected && (
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="font-semibold mb-4">Acțiuni</h3>
            
            <div className="flex flex-wrap gap-3">
              {!indexExists && (
                <button
                  onClick={createIndex}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50"
                >
                  <Database className="w-4 h-4" />
                  Creează Index
                </button>
              )}
              
              {indexExists && !isIndexing && (
                <button
                  onClick={startIndexing}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50"
                >
                  <Play className="w-4 h-4" />
                  Pornește Indexare
                </button>
              )}
              
              {indexExists && (
                <button
                  onClick={deleteIndex}
                  disabled={actionLoading || isIndexing}
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors font-medium disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4" />
                  Șterge Index
                </button>
              )}
              
              {indexExists && !isIndexing && (
                <button
                  onClick={createIndex}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-2 px-4 py-2.5 border border-border rounded-lg hover:bg-muted transition-colors font-medium disabled:opacity-50"
                >
                  <RefreshCw className="w-4 h-4" />
                  Recreează Index
                </button>
              )}
            </div>
            
            {indexExists && (
              <p className="mt-3 text-sm text-muted-foreground">
                <strong>Recomandare:</strong> Rulează indexarea după fiecare sincronizare a bazei de date pentru a menține căutarea actualizată.
              </p>
            )}
          </div>
        )}

        {/* Test Search */}
        {isConnected && indexExists && status.index.docs_count > 0 && (
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-500" />
              Test Căutare Fuzzy
            </h3>
            
            <div className="flex gap-3 mb-4">
              <input
                type="text"
                value={testQuery}
                onChange={(e) => setTestQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && testSearch()}
                placeholder="Caută firme... (ex: Karuful, dedeman, 12345678)"
                className="flex-1 px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
              />
              <button
                onClick={testSearch}
                disabled={searching || !testQuery.trim()}
                className="px-6 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium disabled:opacity-50"
              >
                {searching ? 'Caut...' : 'Caută'}
              </button>
            </div>
            
            {testResults && (
              <div className="space-y-3">
                {testResults.error ? (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                    {testResults.error}
                  </div>
                ) : (
                  <>
                    <p className="text-sm text-muted-foreground">
                      {testResults.data?.pagination?.total.toLocaleString()} rezultate găsite în ~50ms
                    </p>
                    <div className="divide-y divide-border">
                      {testResults.data?.results?.map((result, i) => (
                        <div key={i} className="py-3">
                          <div className="flex items-start justify-between">
                            <div>
                              <h4 
                                className="font-medium"
                                dangerouslySetInnerHTML={{ 
                                  __html: result.denumire_highlight || result.denumire 
                                }}
                              />
                              <p className="text-sm text-muted-foreground">
                                CUI: {result.cui} | {result.localitate}, {result.judet}
                              </p>
                              {result.caen_denumire && (
                                <p className="text-xs text-muted-foreground">
                                  CAEN {result.anaf_cod_caen}: {result.caen_denumire}
                                </p>
                              )}
                            </div>
                            <span className="text-xs bg-muted px-2 py-1 rounded">
                              Score: {result.score?.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        )}

        {/* Configuration Info */}
        {config && (
          <div className="bg-card border border-border rounded-xl p-6">
            <h3 className="font-semibold mb-4">Configurație</h3>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-muted-foreground">Elasticsearch URL</dt>
                <dd className="font-mono">{config.es_host}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Index Name</dt>
                <dd className="font-mono">{config.index_name}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Docker Compose</dt>
                <dd className="font-mono text-xs">{config.docker_compose_path}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Setup Script</dt>
                <dd className="font-mono text-xs">{config.setup_script}</dd>
              </div>
            </dl>
          </div>
        )}
      </div>
    </AdminLayout>
  );
};

export default AdminElasticsearchPage;
