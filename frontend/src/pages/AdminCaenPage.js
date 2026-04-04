import React, { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw, Loader2, Zap, CheckCircle, Upload, Plus, Pencil, Trash2,
  Search, ChevronLeft, ChevronRight, X, FileText, Download
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import AdminLayout from '../components/AdminLayout';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const AdminCaenPage = () => {
  const { token } = useAuth();
  const [stats, setStats] = useState(null);
  const [codes, setCodes] = useState([]);
  const [totalCodes, setTotalCodes] = useState(0);
  const [loading, setLoading] = useState(true);
  const [codesLoading, setCodesLoading] = useState(false);
  const [skip, setSkip] = useState(0);
  const [searchQ, setSearchQ] = useState('');
  const [filter, setFilter] = useState('all');
  const [rev1Running, setRev1Running] = useState(false);
  const [rev1Result, setRev1Result] = useState(null);
  const [editCode, setEditCode] = useState(null);
  const [editName, setEditName] = useState('');
  const [editSectiune, setEditSectiune] = useState('');
  const [saving, setSaving] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [newCod, setNewCod] = useState('');
  const [newName, setNewName] = useState('');
  const [newSectiune, setNewSectiune] = useState('');
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const LIMIT = 50;

  const headers = useCallback(() => ({
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  }), [token]);

  const loadStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/caen/stats`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (res.ok) setStats(await res.json());
    } catch (err) { console.error('Stats error:', err); }
  }, [token]);

  const loadCodes = useCallback(async (s = skip, q = searchQ, f = filter) => {
    setCodesLoading(true);
    try {
      const params = new URLSearchParams({ skip: s, limit: LIMIT, q, filter: f });
      const res = await fetch(`${API_URL}/api/admin/caen/codes?${params}`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setCodes(data.codes || []);
        setTotalCodes(data.total || 0);
      }
    } catch (err) { console.error('Codes error:', err); }
    finally { setCodesLoading(false); }
  }, [token, skip, searchQ, filter]);

  useEffect(() => {
    if (!token) return;
    const init = async () => {
      setLoading(true);
      await loadStats();
      await loadCodes(0, '', 'all');
      setLoading(false);
    };
    init();
  }, [token]);

  useEffect(() => {
    if (!loading) loadCodes(skip, searchQ, filter);
  }, [skip]);

  const handleSearch = () => {
    setSkip(0);
    loadCodes(0, searchQ, filter);
  };

  const handleFilterChange = (f) => {
    setFilter(f);
    setSkip(0);
    loadCodes(0, searchQ, f);
  };

  const runRev1Update = async () => {
    if (!window.confirm('Actualizezi descrierile codurilor CAEN Rev.1? Codurile cu descriere generica vor primi denumirile corecte.')) return;
    setRev1Running(true);
    setRev1Result(null);
    try {
      const res = await fetch(`${API_URL}/api/admin/caen/update-rev1`, { method: 'POST', headers: headers() });
      if (res.ok) {
        const data = await res.json();
        setRev1Result(data);
        loadStats();
        loadCodes(skip, searchQ, filter);
      }
    } catch (err) { console.error('Rev1 error:', err); }
    finally { setRev1Running(false); }
  };

  const startEdit = (code) => {
    setEditCode(code.cod);
    setEditName(code.name || code.denumire || '');
    setEditSectiune(code.sectiune || '');
  };

  const saveEdit = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/caen/codes/${editCode}`, {
        method: 'PUT', headers: headers(),
        body: JSON.stringify({ name: editName, sectiune: editSectiune }),
      });
      if (res.ok) {
        setEditCode(null);
        loadCodes(skip, searchQ, filter);
        loadStats();
      }
    } catch (err) { console.error('Save error:', err); }
    finally { setSaving(false); }
  };

  const addCode = async () => {
    if (!newCod.trim() || !newName.trim()) return;
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/caen/codes`, {
        method: 'POST', headers: headers(),
        body: JSON.stringify({ cod: newCod.trim(), name: newName.trim(), sectiune: newSectiune.trim() }),
      });
      const data = await res.json();
      if (data.error) { alert(data.error); }
      else {
        setShowAdd(false);
        setNewCod(''); setNewName(''); setNewSectiune('');
        loadCodes(skip, searchQ, filter);
        loadStats();
      }
    } catch (err) { console.error('Add error:', err); }
    finally { setSaving(false); }
  };

  const deleteCode = async (cod) => {
    try {
      const res = await fetch(`${API_URL}/api/admin/caen/codes/${cod}`, {
        method: 'DELETE', headers: headers(),
      });
      if (res.ok) {
        setDeleteConfirm(null);
        loadCodes(skip, searchQ, filter);
        loadStats();
      }
    } catch (err) { console.error('Delete error:', err); }
  };

  const handleCsvImport = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_URL}/api/admin/caen/import-csv`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setImportResult(data);
        loadStats();
        loadCodes(skip, searchQ, filter);
      }
    } catch (err) { console.error('Import error:', err); }
    finally { setImporting(false); e.target.value = ''; }
  };

  const totalPages = Math.ceil(totalCodes / LIMIT);
  const currentPage = Math.floor(skip / LIMIT) + 1;

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between" data-testid="admin-caen-header">
          <div>
            <h2 className="text-2xl font-bold">Coduri CAEN</h2>
            <p className="text-muted-foreground">Gestionare nomenclator coduri de activitate economica</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => { loadStats(); loadCodes(skip, searchQ, filter); }}
              className="flex items-center gap-2 px-4 py-2 bg-secondary rounded-lg hover:bg-secondary/80 transition-colors"
              data-testid="caen-refresh-btn"
            >
              <RefreshCw className="w-4 h-4" /> Refresh
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="caen-stats-grid">
          <div className="bg-card border border-border rounded-xl p-5">
            <p className="text-sm text-muted-foreground mb-1">Total Coduri</p>
            <p className="text-3xl font-bold" data-testid="caen-total">{stats?.total?.toLocaleString('ro-RO') || 0}</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-5">
            <p className="text-sm text-muted-foreground mb-1">Descrieri Valide</p>
            <p className="text-3xl font-bold text-green-600" data-testid="caen-valid">{stats?.valid_descriptions?.toLocaleString('ro-RO') || 0}</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-5">
            <p className="text-sm text-muted-foreground mb-1">Descrieri Generice</p>
            <p className="text-3xl font-bold text-amber-600" data-testid="caen-generic">{stats?.generic_descriptions?.toLocaleString('ro-RO') || 0}</p>
          </div>
          <div className="bg-card border border-border rounded-xl p-5">
            <p className="text-sm text-muted-foreground mb-1">Folosite de Firme</p>
            <p className="text-3xl font-bold text-blue-600" data-testid="caen-used">{stats?.used_by_firms?.toLocaleString('ro-RO') || 0}</p>
          </div>
        </div>

        {/* Actions Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Rev.1 Update */}
          <div className="bg-card border border-border rounded-xl p-5" data-testid="rev1-update-section">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" />
              Actualizare Descrieri Rev.1
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Inlocuieste descrierile generice ("Cod CAEN xxxx") cu denumirile oficiale romanesti.
              Mapping: {stats?.rev1_mapping_size || 0} coduri disponibile.
            </p>
            <button
              onClick={runRev1Update}
              disabled={rev1Running}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 transition-colors"
              data-testid="rev1-update-btn"
            >
              {rev1Running ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              {rev1Running ? 'Se proceseaza...' : 'Actualizeaza Rev.1'}
            </button>
            {rev1Result && (
              <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg text-sm" data-testid="rev1-result">
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="font-medium text-green-800">Actualizare completa</span>
                </div>
                <div className="text-green-700 space-y-0.5">
                  <p>Actualizate: <strong>{rev1Result.updated}</strong></p>
                  <p>Inserate noi: <strong>{rev1Result.upserted}</strong></p>
                  <p>Total coduri: <strong>{rev1Result.total}</strong></p>
                  <p>Ramase generice: <strong>{rev1Result.remaining_generic}</strong></p>
                </div>
              </div>
            )}
          </div>

          {/* CSV Import */}
          <div className="bg-card border border-border rounded-xl p-5" data-testid="csv-import-section">
            <h3 className="font-semibold mb-2 flex items-center gap-2">
              <Upload className="w-4 h-4 text-blue-500" />
              Import CSV
            </h3>
            <p className="text-sm text-muted-foreground mb-3">
              Importa coduri CAEN dintr-un fisier CSV. Coloane necesare: <code className="bg-muted px-1 rounded">cod</code>, <code className="bg-muted px-1 rounded">name</code> (optional: <code className="bg-muted px-1 rounded">sectiune</code>).
              Delimitator: virgula, punct-virgula sau tab.
            </p>
            <div className="flex items-center gap-3">
              <label
                className={`flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition-colors ${importing ? 'opacity-50 pointer-events-none' : ''}`}
                data-testid="csv-import-btn"
              >
                {importing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                {importing ? 'Se importa...' : 'Alege fisier CSV'}
                <input type="file" accept=".csv,.txt" className="hidden" onChange={handleCsvImport} disabled={importing} data-testid="csv-file-input" />
              </label>
              <a
                href={`data:text/csv;charset=utf-8,cod;name;sectiune\n0111;Cultivarea cerealelor (exclusiv orez);A\n0112;Cultivarea orezului;A`}
                download="caen_template.csv"
                className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
                data-testid="csv-template-link"
              >
                <Download className="w-3 h-3" /> Template
              </a>
            </div>
            {importResult && (
              <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg text-sm" data-testid="import-result">
                <div className="flex items-center gap-2 mb-1">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="font-medium text-green-800">Import complet</span>
                </div>
                <div className="text-green-700 space-y-0.5">
                  <p>Importate noi: <strong>{importResult.imported}</strong></p>
                  <p>Actualizate: <strong>{importResult.updated}</strong></p>
                  {importResult.total_errors > 0 && (
                    <p className="text-amber-700">Erori: <strong>{importResult.total_errors}</strong></p>
                  )}
                  <p>Total coduri in DB: <strong>{importResult.total_codes}</strong></p>
                </div>
                {importResult.errors?.length > 0 && (
                  <div className="mt-2 max-h-24 overflow-y-auto text-xs text-red-600">
                    {importResult.errors.map((e, i) => <p key={i}>{e}</p>)}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Codes Table */}
        <div className="bg-card border border-border rounded-xl p-5" data-testid="caen-codes-table-section">
          {/* Search & Filter Bar */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-4">
            <div className="flex items-center gap-2 flex-1 w-full sm:w-auto">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Cauta dupa cod sau denumire..."
                  value={searchQ}
                  onChange={(e) => setSearchQ(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  className="w-full pl-9 pr-3 py-2 bg-background border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                  data-testid="caen-search-input"
                />
              </div>
              <button
                onClick={handleSearch}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm hover:bg-primary/90 transition-colors"
                data-testid="caen-search-btn"
              >
                Cauta
              </button>
            </div>

            <div className="flex items-center gap-2">
              {[
                { key: 'all', label: 'Toate' },
                { key: 'valid', label: 'Valide', cls: 'bg-green-100 text-green-700 border-green-200' },
                { key: 'generic', label: 'Generice', cls: 'bg-amber-100 text-amber-700 border-amber-200' },
              ].map(f => (
                <button
                  key={f.key}
                  onClick={() => handleFilterChange(f.key)}
                  className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                    filter === f.key
                      ? (f.cls || 'bg-primary text-primary-foreground border-primary')
                      : 'bg-secondary text-muted-foreground border-border hover:bg-secondary/80'
                  }`}
                  data-testid={`caen-filter-${f.key}`}
                >
                  {f.label}
                </button>
              ))}
              <button
                onClick={() => setShowAdd(true)}
                className="flex items-center gap-1 px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs hover:bg-green-700 transition-colors"
                data-testid="caen-add-btn"
              >
                <Plus className="w-3 h-3" /> Adauga
              </button>
            </div>
          </div>

          {/* Add Form */}
          {showAdd && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg" data-testid="caen-add-form">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-green-800">Adauga Cod CAEN Nou</h4>
                <button onClick={() => setShowAdd(false)} className="text-muted-foreground hover:text-foreground">
                  <X className="w-4 h-4" />
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <input
                  placeholder="Cod (ex: 0111)"
                  value={newCod}
                  onChange={(e) => setNewCod(e.target.value)}
                  className="px-3 py-2 bg-white border border-green-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-300"
                  data-testid="caen-add-cod"
                />
                <input
                  placeholder="Denumire activitate"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="sm:col-span-2 px-3 py-2 bg-white border border-green-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-300"
                  data-testid="caen-add-name"
                />
                <div className="flex gap-2">
                  <input
                    placeholder="Sect. (A-U)"
                    value={newSectiune}
                    onChange={(e) => setNewSectiune(e.target.value)}
                    className="flex-1 px-3 py-2 bg-white border border-green-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-300"
                    data-testid="caen-add-sectiune"
                  />
                  <button
                    onClick={addCode}
                    disabled={saving || !newCod.trim() || !newName.trim()}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 disabled:opacity-50 transition-colors"
                    data-testid="caen-add-submit"
                  >
                    {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Salveaza'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Table info */}
          <div className="flex items-center justify-between mb-2 text-sm text-muted-foreground">
            <span data-testid="caen-table-info">{totalCodes.toLocaleString('ro-RO')} coduri gasite</span>
            <span>Pagina {currentPage} / {totalPages || 1}</span>
          </div>

          {/* Table */}
          <div className="border border-border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm" data-testid="caen-codes-table">
                <thead className="bg-muted/50">
                  <tr>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground w-24">Cod</th>
                    <th className="text-left px-4 py-3 font-medium text-muted-foreground">Denumire</th>
                    <th className="text-center px-4 py-3 font-medium text-muted-foreground w-20">Sectiune</th>
                    <th className="text-center px-4 py-3 font-medium text-muted-foreground w-20">Status</th>
                    <th className="text-center px-4 py-3 font-medium text-muted-foreground w-28">Actiuni</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {codesLoading ? (
                    <tr>
                      <td colSpan={5} className="text-center py-10">
                        <Loader2 className="w-6 h-6 animate-spin text-primary mx-auto" />
                      </td>
                    </tr>
                  ) : codes.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center py-10 text-muted-foreground">
                        <FileText className="w-8 h-8 mx-auto mb-2 opacity-40" />
                        Niciun cod gasit
                      </td>
                    </tr>
                  ) : codes.map((code) => {
                    const isGeneric = (code.name || '').startsWith('Cod CAEN ');
                    const isEditing = editCode === code.cod;

                    return (
                      <tr key={code.cod} className="hover:bg-muted/20 transition-colors" data-testid={`caen-row-${code.cod}`}>
                        <td className="px-4 py-2.5 font-mono font-medium">{code.cod}</td>
                        <td className="px-4 py-2.5">
                          {isEditing ? (
                            <input
                              value={editName}
                              onChange={(e) => setEditName(e.target.value)}
                              className="w-full px-2 py-1 bg-background border border-primary/30 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                              data-testid="caen-edit-name-input"
                              autoFocus
                            />
                          ) : (
                            <span className={isGeneric ? 'text-amber-600 italic' : ''}>
                              {(code.name || code.denumire || '-').length > 90
                                ? (code.name || code.denumire || '').slice(0, 90) + '...'
                                : (code.name || code.denumire || '-')}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2.5 text-center">
                          {isEditing ? (
                            <input
                              value={editSectiune}
                              onChange={(e) => setEditSectiune(e.target.value)}
                              className="w-14 px-2 py-1 bg-background border border-primary/30 rounded text-sm text-center focus:outline-none"
                              data-testid="caen-edit-sectiune-input"
                            />
                          ) : (
                            <span className="inline-block px-2 py-0.5 bg-muted rounded text-xs font-mono">
                              {code.sectiune || '-'}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-2.5 text-center">
                          <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                            isGeneric ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
                          }`}>
                            {isGeneric ? 'GENERIC' : 'OK'}
                          </span>
                        </td>
                        <td className="px-4 py-2.5 text-center">
                          {isEditing ? (
                            <div className="flex items-center justify-center gap-1">
                              <button
                                onClick={saveEdit}
                                disabled={saving}
                                className="px-2 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700 disabled:opacity-50"
                                data-testid="caen-edit-save"
                              >
                                {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Salveaza'}
                              </button>
                              <button
                                onClick={() => setEditCode(null)}
                                className="px-2 py-1 bg-secondary text-muted-foreground rounded text-xs hover:bg-secondary/80"
                                data-testid="caen-edit-cancel"
                              >
                                Anuleaza
                              </button>
                            </div>
                          ) : deleteConfirm === code.cod ? (
                            <div className="flex items-center justify-center gap-1">
                              <button
                                onClick={() => deleteCode(code.cod)}
                                className="px-2 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700"
                                data-testid="caen-delete-confirm"
                              >
                                Sterge
                              </button>
                              <button
                                onClick={() => setDeleteConfirm(null)}
                                className="px-2 py-1 bg-secondary text-muted-foreground rounded text-xs hover:bg-secondary/80"
                                data-testid="caen-delete-cancel"
                              >
                                Nu
                              </button>
                            </div>
                          ) : (
                            <div className="flex items-center justify-center gap-1">
                              <button
                                onClick={() => startEdit(code)}
                                className="p-1.5 hover:bg-blue-100 rounded transition-colors"
                                title="Editeaza"
                                data-testid={`caen-edit-${code.cod}`}
                              >
                                <Pencil className="w-3.5 h-3.5 text-blue-600" />
                              </button>
                              <button
                                onClick={() => setDeleteConfirm(code.cod)}
                                className="p-1.5 hover:bg-red-100 rounded transition-colors"
                                title="Sterge"
                                data-testid={`caen-delete-${code.cod}`}
                              >
                                <Trash2 className="w-3.5 h-3.5 text-red-600" />
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4" data-testid="caen-pagination">
              <button
                onClick={() => setSkip(Math.max(0, skip - LIMIT))}
                disabled={skip === 0}
                className="flex items-center gap-1 px-3 py-1.5 bg-secondary rounded-lg text-sm disabled:opacity-50 hover:bg-secondary/80 transition-colors"
                data-testid="caen-prev-page"
              >
                <ChevronLeft className="w-4 h-4" /> Inapoi
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let page;
                  if (totalPages <= 5) {
                    page = i + 1;
                  } else if (currentPage <= 3) {
                    page = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    page = totalPages - 4 + i;
                  } else {
                    page = currentPage - 2 + i;
                  }
                  return (
                    <button
                      key={page}
                      onClick={() => setSkip((page - 1) * LIMIT)}
                      className={`w-8 h-8 rounded-lg text-xs transition-colors ${
                        currentPage === page ? 'bg-primary text-primary-foreground' : 'bg-secondary hover:bg-secondary/80'
                      }`}
                    >
                      {page}
                    </button>
                  );
                })}
              </div>
              <button
                onClick={() => setSkip(skip + LIMIT)}
                disabled={currentPage >= totalPages}
                className="flex items-center gap-1 px-3 py-1.5 bg-secondary rounded-lg text-sm disabled:opacity-50 hover:bg-secondary/80 transition-colors"
                data-testid="caen-next-page"
              >
                Inainte <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminCaenPage;
