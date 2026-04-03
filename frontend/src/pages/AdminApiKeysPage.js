import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import AdminLayout from '../components/AdminLayout';
import { 
  Key, Search, ToggleLeft, ToggleRight, Activity, 
  Users, RefreshCw, Plus, Edit2, Copy, Check, X, AlertCircle
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const API_PLANS = [
  { id: 'basic', name: 'Basic', requests_per_day: 100, requests_per_month: 3000 },
  { id: 'pro', name: 'Pro', requests_per_day: 1000, requests_per_month: 30000 },
  { id: 'enterprise', name: 'Enterprise', requests_per_day: 10000, requests_per_month: 300000 }
];

const AdminApiKeysPage = () => {
  const navigate = useNavigate();
  const { user, token, isAuthenticated, loading: authLoading } = useAuth();
  
  const [keys, setKeys] = useState([]);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPlan, setFilterPlan] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingKey, setEditingKey] = useState(null);
  const [newKeyData, setNewKeyData] = useState(null);
  const [copiedKey, setCopiedKey] = useState(null);
  
  // Form states
  const [createForm, setCreateForm] = useState({
    user_email: '',
    name: '',
    plan_id: 'basic',
    custom_requests_per_day: '',
    custom_requests_per_month: ''
  });
  
  const [editForm, setEditForm] = useState({
    name: '',
    plan_id: '',
    custom_requests_per_day: '',
    custom_requests_per_month: '',
    active: true
  });
  
  const [saving, setSaving] = useState(false);

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
    fetchAllKeys();
    fetchUsers();
  }, [isAuthenticated, user, navigate, authLoading]);

  const fetchAllKeys = async () => {
    try {
      const res = await fetch(`${API_URL}/api/api-keys/admin/all`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setKeys(data.keys || []);
        setStats(data.stats || null);
      }
    } catch (error) {
      console.error('Failed to fetch keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_URL}/api/api-keys/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUsers(data.users || []);
      }
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
  };

  const toggleKey = async (keyId) => {
    try {
      const res = await fetch(`${API_URL}/api/api-keys/admin/${keyId}/toggle`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchAllKeys();
      }
    } catch (error) {
      console.error('Failed to toggle key:', error);
    }
  };

  const createKey = async () => {
    if (!createForm.user_email || !createForm.name) {
      alert('Completează email-ul și numele cheii');
      return;
    }
    
    setSaving(true);
    try {
      const payload = {
        user_email: createForm.user_email,
        name: createForm.name,
        plan_id: createForm.plan_id
      };
      
      if (createForm.custom_requests_per_day) {
        payload.custom_requests_per_day = parseInt(createForm.custom_requests_per_day);
      }
      if (createForm.custom_requests_per_month) {
        payload.custom_requests_per_month = parseInt(createForm.custom_requests_per_month);
      }
      
      const res = await fetch(`${API_URL}/api/api-keys/admin/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        const data = await res.json();
        setNewKeyData(data);
        setShowCreateModal(false);
        setCreateForm({
          user_email: '',
          name: '',
          plan_id: 'basic',
          custom_requests_per_day: '',
          custom_requests_per_month: ''
        });
        fetchAllKeys();
      } else {
        const error = await res.json();
        alert(error.detail || 'Eroare la creare');
      }
    } catch (error) {
      console.error('Failed to create key:', error);
      alert('Eroare la creare');
    } finally {
      setSaving(false);
    }
  };

  const openEditModal = (key) => {
    setEditingKey(key);
    setEditForm({
      name: key.name || '',
      plan_id: key.plan_id || 'basic',
      custom_requests_per_day: key.custom_requests_per_day || '',
      custom_requests_per_month: key.custom_requests_per_month || '',
      active: key.active
    });
    setShowEditModal(true);
  };

  const updateKey = async () => {
    if (!editingKey) return;
    
    setSaving(true);
    try {
      const payload = {};
      
      if (editForm.name !== editingKey.name) {
        payload.name = editForm.name;
      }
      if (editForm.plan_id !== editingKey.plan_id) {
        payload.plan_id = editForm.plan_id;
      }
      if (editForm.active !== editingKey.active) {
        payload.active = editForm.active;
      }
      
      // Handle custom limits - convert to int or null
      const newDaily = editForm.custom_requests_per_day ? parseInt(editForm.custom_requests_per_day) : null;
      const newMonthly = editForm.custom_requests_per_month ? parseInt(editForm.custom_requests_per_month) : null;
      
      if (newDaily !== editingKey.custom_requests_per_day) {
        payload.custom_requests_per_day = newDaily || 0; // 0 means use plan default
      }
      if (newMonthly !== editingKey.custom_requests_per_month) {
        payload.custom_requests_per_month = newMonthly || 0;
      }
      
      const res = await fetch(`${API_URL}/api/api-keys/admin/${editingKey.id}/update`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      
      if (res.ok) {
        setShowEditModal(false);
        setEditingKey(null);
        fetchAllKeys();
      } else {
        const error = await res.json();
        alert(error.detail || 'Eroare la actualizare');
      }
    } catch (error) {
      console.error('Failed to update key:', error);
      alert('Eroare la actualizare');
    } finally {
      setSaving(false);
    }
  };

  const copyToClipboard = (text, keyId) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(keyId);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const getPlanBadgeColor = (planId) => {
    switch (planId) {
      case 'basic': return 'bg-gray-100 text-gray-700';
      case 'pro': return 'bg-blue-100 text-blue-700';
      case 'enterprise': return 'bg-purple-100 text-purple-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  // Filter keys
  const filteredKeys = keys.filter(key => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      if (!key.name?.toLowerCase().includes(query) && 
          !key.user_email?.toLowerCase().includes(query) &&
          !key.key_preview?.toLowerCase().includes(query)) {
        return false;
      }
    }
    
    if (filterPlan !== 'all' && key.plan_id !== filterPlan) {
      return false;
    }
    
    if (filterStatus === 'active' && !key.active) return false;
    if (filterStatus === 'inactive' && key.active) return false;
    if (filterStatus === 'revoked' && !key.revoked) return false;
    
    return true;
  });

  if (loading || authLoading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <Helmet>
        <title>Gestionare Chei API | Admin RapoarteFirme</title>
      </Helmet>

      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Gestionare Chei API</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Vizualizează și gestionează toate cheile API ale utilizatorilor
            </p>
          </div>
          <div className="mt-4 sm:mt-0 flex gap-2">
            <button
              onClick={() => setShowCreateModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm"
              data-testid="admin-create-key-btn"
            >
              <Plus className="w-4 h-4" />
              Adaugă cheie
            </button>
            <button
              onClick={fetchAllKeys}
              className="inline-flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-muted transition-colors text-sm"
            >
              <RefreshCw className="w-4 h-4" />
              Reîncarcă
            </button>
          </div>
        </div>

        {/* New Key Alert */}
        {newKeyData && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6" data-testid="new-key-alert">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <Key className="w-5 h-5 text-green-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-green-800 mb-1">Cheie API creată pentru {newKeyData.user_email}!</h3>
                <p className="text-sm text-green-700 mb-3">
                  Copiază cheia și transmite-o utilizatorului - nu o vei mai putea vedea din nou!
                </p>
                <div className="flex items-center gap-2 bg-white border border-green-200 rounded-lg p-3">
                  <code className="flex-1 text-sm font-mono text-green-800 break-all">
                    {newKeyData.api_key}
                  </code>
                  <button
                    onClick={() => copyToClipboard(newKeyData.api_key, 'new')}
                    className="p-2 hover:bg-green-100 rounded-lg transition-colors"
                  >
                    {copiedKey === 'new' ? (
                      <Check className="w-5 h-5 text-green-600" />
                    ) : (
                      <Copy className="w-5 h-5 text-green-600" />
                    )}
                  </button>
                </div>
                <button
                  onClick={() => setNewKeyData(null)}
                  className="mt-3 text-sm text-green-700 hover:text-green-800 underline"
                >
                  Am salvat cheia, închide
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Key className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <div className="text-2xl font-semibold">{stats.total_keys}</div>
                  <div className="text-xs text-muted-foreground">Total chei</div>
                </div>
              </div>
            </div>
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <ToggleRight className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <div className="text-2xl font-semibold">{stats.active_keys}</div>
                  <div className="text-xs text-muted-foreground">Chei active</div>
                </div>
              </div>
            </div>
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
                  <Activity className="w-5 h-5 text-amber-600" />
                </div>
                <div>
                  <div className="text-2xl font-semibold">{stats.total_requests_today.toLocaleString()}</div>
                  <div className="text-xs text-muted-foreground">Requests azi</div>
                </div>
              </div>
            </div>
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <Users className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <div className="text-2xl font-semibold">
                    {new Set(keys.map(k => k.user_id)).size}
                  </div>
                  <div className="text-xs text-muted-foreground">Utilizatori cu chei</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Caută după nume, email sau cheie..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none text-sm"
                data-testid="search-keys-input"
              />
            </div>
            <div className="flex gap-3">
              <select
                value={filterPlan}
                onChange={(e) => setFilterPlan(e.target.value)}
                className="px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none text-sm"
              >
                <option value="all">Toate planurile</option>
                <option value="basic">Basic</option>
                <option value="pro">Pro</option>
                <option value="enterprise">Enterprise</option>
              </select>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none text-sm"
              >
                <option value="all">Toate statusurile</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
                <option value="revoked">Revocate</option>
              </select>
            </div>
          </div>
        </div>

        {/* Keys Table */}
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-muted/50 border-b border-border">
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Cheie</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Utilizator</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Plan</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Limite (zi/lună)</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Utilizare azi</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Total</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-muted-foreground uppercase">Acțiuni</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredKeys.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-12 text-center text-muted-foreground">
                      {searchQuery || filterPlan !== 'all' || filterStatus !== 'all'
                        ? 'Nicio cheie găsită cu filtrele selectate'
                        : 'Nu există chei API create încă'
                      }
                    </td>
                  </tr>
                ) : (
                  filteredKeys.map((key) => (
                    <tr key={key.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-4 py-3">
                        <div>
                          <div className="font-medium text-sm">{key.name}</div>
                          <code className="text-xs text-muted-foreground">{key.key_preview}</code>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm">{key.user_email}</div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 text-xs font-medium rounded-lg ${getPlanBadgeColor(key.plan_id)}`}>
                          {key.plan_name}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm">
                          <span className={key.has_custom_limits ? 'text-amber-600 font-medium' : ''}>
                            {key.requests_per_day.toLocaleString()} / {key.requests_per_month.toLocaleString()}
                          </span>
                          {key.has_custom_limits && (
                            <span className="ml-1 text-xs text-amber-600">(custom)</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm font-medium">
                          {key.requests_today.toLocaleString()} / {key.requests_per_day.toLocaleString()}
                        </div>
                        <div className="mt-1 h-1.5 w-20 bg-muted rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 rounded-full"
                            style={{ width: `${Math.min((key.requests_today / key.requests_per_day) * 100, 100)}%` }}
                          />
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="text-sm text-muted-foreground">{key.requests_total.toLocaleString()}</div>
                      </td>
                      <td className="px-4 py-3">
                        {key.revoked ? (
                          <span className="px-2 py-1 text-xs font-medium rounded-lg bg-red-100 text-red-700">
                            Revocat
                          </span>
                        ) : key.active ? (
                          <span className="px-2 py-1 text-xs font-medium rounded-lg bg-green-100 text-green-700">
                            Activ
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs font-medium rounded-lg bg-gray-100 text-gray-700">
                            Inactiv
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => openEditModal(key)}
                            className="p-2 hover:bg-blue-100 text-blue-600 rounded-lg transition-colors"
                            title="Editează"
                            data-testid={`edit-key-${key.id}`}
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          {!key.revoked && (
                            <button
                              onClick={() => toggleKey(key.id)}
                              className={`p-2 rounded-lg transition-colors ${
                                key.active 
                                  ? 'hover:bg-amber-100 text-amber-600' 
                                  : 'hover:bg-green-100 text-green-600'
                              }`}
                              title={key.active ? 'Dezactivează' : 'Activează'}
                              data-testid={`toggle-key-${key.id}`}
                            >
                              {key.active ? (
                                <ToggleRight className="w-5 h-5" />
                              ) : (
                                <ToggleLeft className="w-5 h-5" />
                              )}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Summary */}
        <div className="text-sm text-muted-foreground text-center">
          Afișare {filteredKeys.length} din {keys.length} chei API
        </div>
      </div>

      {/* Create Key Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-xl shadow-xl max-w-lg w-full p-6" data-testid="create-key-modal">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Adaugă cheie API nouă</h2>
              <button onClick={() => setShowCreateModal(false)} className="p-2 hover:bg-muted rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5">Utilizator *</label>
                <select
                  value={createForm.user_email}
                  onChange={(e) => setCreateForm({...createForm, user_email: e.target.value})}
                  className="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                  data-testid="create-user-select"
                >
                  <option value="">-- Selectează utilizator --</option>
                  {users.map(u => (
                    <option key={u.id} value={u.email}>{u.email} ({u.name})</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1.5">Nume cheie *</label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({...createForm, name: e.target.value})}
                  placeholder="ex: Aplicația mea, Server producție"
                  className="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                  data-testid="create-name-input"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1.5">Plan API</label>
                <select
                  value={createForm.plan_id}
                  onChange={(e) => setCreateForm({...createForm, plan_id: e.target.value})}
                  className="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                  data-testid="create-plan-select"
                >
                  {API_PLANS.map(plan => (
                    <option key={plan.id} value={plan.id}>
                      {plan.name} ({plan.requests_per_day.toLocaleString()} req/zi, {plan.requests_per_month.toLocaleString()} req/lună)
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <div className="flex items-start gap-2 mb-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm font-medium text-amber-800">Limite custom (opțional)</span>
                </div>
                <p className="text-xs text-amber-700 mb-3">Lasă gol pentru a folosi limitele standard ale planului</p>
                
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1 text-amber-800">Requests / zi</label>
                    <input
                      type="number"
                      value={createForm.custom_requests_per_day}
                      onChange={(e) => setCreateForm({...createForm, custom_requests_per_day: e.target.value})}
                      placeholder="ex: 500"
                      className="w-full px-3 py-2 border border-amber-200 rounded-lg focus:ring-2 focus:ring-amber-200 focus:border-amber-400 outline-none text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1 text-amber-800">Requests / lună</label>
                    <input
                      type="number"
                      value={createForm.custom_requests_per_month}
                      onChange={(e) => setCreateForm({...createForm, custom_requests_per_month: e.target.value})}
                      placeholder="ex: 15000"
                      className="w-full px-3 py-2 border border-amber-200 rounded-lg focus:ring-2 focus:ring-amber-200 focus:border-amber-400 outline-none text-sm"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2.5 border border-border rounded-lg hover:bg-muted transition-colors font-medium text-sm"
              >
                Anulează
              </button>
              <button
                onClick={createKey}
                disabled={!createForm.user_email || !createForm.name || saving}
                className="flex-1 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium text-sm disabled:opacity-50"
                data-testid="confirm-create-key-btn"
              >
                {saving ? 'Se creează...' : 'Creează cheie'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Key Modal */}
      {showEditModal && editingKey && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-xl shadow-xl max-w-lg w-full p-6" data-testid="edit-key-modal">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Editează cheie API</h2>
              <button onClick={() => setShowEditModal(false)} className="p-2 hover:bg-muted rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="mb-4 p-3 bg-muted/50 rounded-lg">
              <div className="text-sm text-muted-foreground">Utilizator: <span className="font-medium text-foreground">{editingKey.user_email}</span></div>
              <code className="text-xs text-muted-foreground">{editingKey.key_preview}</code>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5">Nume cheie</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                  className="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                  data-testid="edit-name-input"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1.5">Plan API</label>
                <select
                  value={editForm.plan_id}
                  onChange={(e) => setEditForm({...editForm, plan_id: e.target.value})}
                  className="w-full px-4 py-2.5 border border-border rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                  data-testid="edit-plan-select"
                >
                  {API_PLANS.map(plan => (
                    <option key={plan.id} value={plan.id}>
                      {plan.name} ({plan.requests_per_day.toLocaleString()} req/zi)
                    </option>
                  ))}
                </select>
              </div>
              
              <div className="flex items-center gap-3">
                <label className="text-sm font-medium">Status:</label>
                <button
                  onClick={() => setEditForm({...editForm, active: !editForm.active})}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    editForm.active 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {editForm.active ? 'Activ' : 'Inactiv'}
                </button>
              </div>
              
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <div className="flex items-start gap-2 mb-2">
                  <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm font-medium text-amber-800">Limite custom</span>
                </div>
                <p className="text-xs text-amber-700 mb-3">Lasă gol (sau 0) pentru a folosi limitele standard ale planului</p>
                
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium mb-1 text-amber-800">Requests / zi</label>
                    <input
                      type="number"
                      value={editForm.custom_requests_per_day}
                      onChange={(e) => setEditForm({...editForm, custom_requests_per_day: e.target.value})}
                      placeholder="Plan default"
                      className="w-full px-3 py-2 border border-amber-200 rounded-lg focus:ring-2 focus:ring-amber-200 focus:border-amber-400 outline-none text-sm"
                      data-testid="edit-daily-limit"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium mb-1 text-amber-800">Requests / lună</label>
                    <input
                      type="number"
                      value={editForm.custom_requests_per_month}
                      onChange={(e) => setEditForm({...editForm, custom_requests_per_month: e.target.value})}
                      placeholder="Plan default"
                      className="w-full px-3 py-2 border border-amber-200 rounded-lg focus:ring-2 focus:ring-amber-200 focus:border-amber-400 outline-none text-sm"
                      data-testid="edit-monthly-limit"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowEditModal(false)}
                className="flex-1 px-4 py-2.5 border border-border rounded-lg hover:bg-muted transition-colors font-medium text-sm"
              >
                Anulează
              </button>
              <button
                onClick={updateKey}
                disabled={saving}
                className="flex-1 px-4 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium text-sm disabled:opacity-50"
                data-testid="confirm-edit-key-btn"
              >
                {saving ? 'Se salvează...' : 'Salvează modificări'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
};

export default AdminApiKeysPage;
