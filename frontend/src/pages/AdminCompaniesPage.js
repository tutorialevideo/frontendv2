import React, { useState, useEffect, useCallback } from 'react';
import { Helmet } from 'react-helmet-async';
import { useAuth } from '../contexts/AuthContext';
import AdminLayout from '../components/AdminLayout';
import { 
  Search, 
  Edit, 
  Eye, 
  Save, 
  X, 
  Building2, 
  AlertCircle,
  CheckCircle,
  XCircle,
  FileText,
  Receipt,
  Activity,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Filter
} from 'lucide-react';

const AdminCompaniesPage = () => {
  const { token } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companyDetails, setCompanyDetails] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [overrides, setOverrides] = useState({});
  const [fieldVisibility, setFieldVisibility] = useState({});
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [filters, setFilters] = useState({
    hasBilant: null,
    isActive: null,
    hasBPI: null
  });

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';
  const PAGE_SIZE = 50;

  const loadCompanies = useCallback(async (searchTerm = '', pageNum = 1) => {
    setLoading(true);
    try {
      const skip = (pageNum - 1) * PAGE_SIZE;
      const res = await fetch(`${API_URL}/api/admin/companies/list?skip=${skip}&limit=${PAGE_SIZE}&q=${encodeURIComponent(searchTerm)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setCompanies(data.companies || []);
        setTotalCount(data.total || 0);
      }
    } catch (error) {
      console.error('Failed to load companies:', error);
    } finally {
      setLoading(false);
    }
  }, [API_URL, token]);

  useEffect(() => {
    if (token) {
      loadCompanies('', 1);
    }
  }, [token, loadCompanies]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadCompanies(searchQuery, 1);
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
    loadCompanies(searchQuery, newPage);
  };

  const loadCompanyDetails = async (cui) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/companies/details/${cui}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setCompanyDetails(data);
        setSelectedCompany(data.raw_data);
        
        const overridesMap = {};
        data.overrides?.forEach(o => {
          overridesMap[o.field_name] = o.override_value;
        });
        setOverrides(overridesMap);
        
        const visibilityMap = {};
        data.field_visibility?.forEach(v => {
          visibilityMap[v.field_name] = v.visibility;
        });
        setFieldVisibility(visibilityMap);
      }
    } catch (error) {
      console.error('Failed to load company details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveOverrides = async () => {
    if (!selectedCompany) return;

    setSaveLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/companies/override`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          cui: selectedCompany.cui,
          overrides: overrides,
          notes: 'Updated from admin panel'
        })
      });

      if (res.ok) {
        alert('Modificările au fost salvate cu succes!');
        setEditMode(false);
        loadCompanyDetails(selectedCompany.cui);
      }
    } catch (error) {
      console.error('Failed to save overrides:', error);
      alert('Eroare la salvarea modificărilor');
    } finally {
      setSaveLoading(false);
    }
  };

  const handleSetFieldVisibility = async (fieldName, visibility) => {
    if (!selectedCompany) return;

    try {
      const res = await fetch(`${API_URL}/api/admin/companies/field-visibility`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          cui: selectedCompany.cui,
          field_name: fieldName,
          visibility: visibility
        })
      });

      if (res.ok) {
        setFieldVisibility(prev => ({ ...prev, [fieldName]: visibility }));
        alert(`Câmpul ${fieldName} setat ca ${visibility}`);
      }
    } catch (error) {
      console.error('Failed to set field visibility:', error);
    }
  };

  // Status badge component
  const StatusBadge = ({ active, label }) => (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
      active 
        ? 'bg-green-100 text-green-700' 
        : 'bg-gray-100 text-gray-500'
    }`}>
      {active ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
      {label}
    </span>
  );

  const renderFieldEditor = (fieldName, value) => {
    const currentVisibility = fieldVisibility[fieldName] || 'public';
    const hasOverride = fieldName in overrides;
    const displayValue = hasOverride ? overrides[fieldName] : value;

    return (
      <div key={fieldName} className="border-b border-border last:border-0 py-3">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <label className="text-sm font-medium">{fieldName}</label>
              {hasOverride && (
                <span className="px-2 py-0.5 text-xs bg-amber-500/10 text-amber-700 rounded">
                  Override
                </span>
              )}
            </div>
            
            {editMode ? (
              <input
                type="text"
                value={displayValue || ''}
                onChange={(e) => setOverrides(prev => ({ ...prev, [fieldName]: e.target.value }))}
                className="w-full px-3 py-2 border border-border rounded-lg focus:outline-none focus:border-primary bg-background text-sm"
              />
            ) : (
              <div className="text-sm text-muted-foreground">{String(displayValue) || '-'}</div>
            )}
          </div>

          <div className="flex items-center space-x-2 ml-4">
            <select
              value={currentVisibility}
              onChange={(e) => handleSetFieldVisibility(fieldName, e.target.value)}
              className="text-xs px-2 py-1 border border-border rounded bg-background"
            >
              <option value="public">Public</option>
              <option value="premium">Premium</option>
              <option value="hidden">Ascuns</option>
            </select>
          </div>
        </div>
      </div>
    );
  };

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  return (
    <AdminLayout>
      <Helmet>
        <title>Gestionare Firme | Admin mFirme</title>
      </Helmet>

      <div className="mb-6">
        <h1 className="text-3xl font-semibold tracking-tight mb-2">Gestionare Firme</h1>
        <p className="text-muted-foreground">
          Vizualizare și editare date firme • {totalCount.toLocaleString('ro-RO')} firme în total
        </p>
      </div>

      {/* Search & Filters */}
      <div className="bg-card border border-border rounded-xl p-4 mb-6">
        <form onSubmit={handleSearch} className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Caută după CUI sau denumire firmă..."
              className="w-full pl-10 pr-4 py-2.5 border border-border rounded-lg focus:outline-none focus:border-primary bg-background"
              data-testid="admin-company-search-input"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center gap-2"
            data-testid="admin-company-search-button"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            Caută
          </button>
        </form>
      </div>

      {/* Companies Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden mb-6">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-semibold">Firmă</th>
                <th className="text-left px-4 py-3 text-sm font-semibold">CUI</th>
                <th className="text-left px-4 py-3 text-sm font-semibold">Județ</th>
                <th className="text-center px-4 py-3 text-sm font-semibold">
                  <span className="flex items-center justify-center gap-1">
                    <FileText className="w-4 h-4" />
                    Bilanț
                  </span>
                </th>
                <th className="text-center px-4 py-3 text-sm font-semibold">
                  <span className="flex items-center justify-center gap-1">
                    <Activity className="w-4 h-4" />
                    ANAF Activ
                  </span>
                </th>
                <th className="text-center px-4 py-3 text-sm font-semibold">
                  <span className="flex items-center justify-center gap-1">
                    <Receipt className="w-4 h-4" />
                    TVA
                  </span>
                </th>
                <th className="text-center px-4 py-3 text-sm font-semibold">
                  <span className="flex items-center justify-center gap-1">
                    <Building2 className="w-4 h-4" />
                    BPI
                  </span>
                </th>
                <th className="text-right px-4 py-3 text-sm font-semibold">CA (RON)</th>
                <th className="text-center px-4 py-3 text-sm font-semibold">Acțiuni</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading && companies.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-4 py-12 text-center">
                    <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-muted-foreground" />
                    <p className="text-muted-foreground">Se încarcă...</p>
                  </td>
                </tr>
              ) : companies.length === 0 ? (
                <tr>
                  <td colSpan="9" className="px-4 py-12 text-center">
                    <Building2 className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">Niciun rezultat găsit</p>
                  </td>
                </tr>
              ) : (
                companies.map((company) => (
                  <tr 
                    key={company.cui} 
                    className={`hover:bg-muted/30 transition-colors ${
                      selectedCompany?.cui === company.cui ? 'bg-primary/5' : ''
                    }`}
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-sm">{company.denumire}</div>
                      <div className="text-xs text-muted-foreground">{company.localitate}</div>
                    </td>
                    <td className="px-4 py-3 font-mono text-sm">{company.cui}</td>
                    <td className="px-4 py-3 text-sm">{company.judet}</td>
                    <td className="px-4 py-3 text-center">
                      {company.mf_an_bilant ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          <CheckCircle className="w-3 h-3" />
                          {company.mf_an_bilant}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                          <XCircle className="w-3 h-3" />
                          Nu
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {company.anaf_stare_startswith_inregistrat ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          <CheckCircle className="w-3 h-3" />
                          Da
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                          <XCircle className="w-3 h-3" />
                          Nu
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {company.anaf_platitor_tva || company.mf_platitor_tva ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                          <CheckCircle className="w-3 h-3" />
                          Da
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                          <XCircle className="w-3 h-3" />
                          Nu
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {company.has_bpi ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                          <CheckCircle className="w-3 h-3" />
                          Da
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                          <XCircle className="w-3 h-3" />
                          Nu
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      {company.mf_cifra_afaceri 
                        ? Number(company.mf_cifra_afaceri).toLocaleString('ro-RO')
                        : '-'
                      }
                    </td>
                    <td className="px-4 py-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          onClick={() => loadCompanyDetails(company.cui)}
                          className="p-2 hover:bg-muted rounded-lg transition-colors"
                          title="Vezi detalii"
                          data-testid="admin-company-view-button"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            loadCompanyDetails(company.cui);
                            setEditMode(true);
                          }}
                          className="p-2 hover:bg-muted rounded-lg transition-colors"
                          title="Editează"
                          data-testid="admin-company-edit-button"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border bg-muted/30">
            <div className="text-sm text-muted-foreground">
              Pagina {page} din {totalPages} • {totalCount.toLocaleString('ro-RO')} firme
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handlePageChange(page - 1)}
                disabled={page === 1 || loading}
                className="p-2 border border-border rounded-lg hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              
              {/* Page numbers */}
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (page <= 3) {
                    pageNum = i + 1;
                  } else if (page >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = page - 2 + i;
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      disabled={loading}
                      className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                        page === pageNum 
                          ? 'bg-primary text-primary-foreground' 
                          : 'hover:bg-muted'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => handlePageChange(page + 1)}
                disabled={page === totalPages || loading}
                className="p-2 border border-border rounded-lg hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Company Details Panel */}
      {selectedCompany && (
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="p-6 border-b border-border">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-semibold mb-1">{selectedCompany.denumire}</h2>
                <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                  <span>CUI: {selectedCompany.cui}</span>
                  <span>•</span>
                  <span>{selectedCompany.judet}, {selectedCompany.localitate}</span>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {!editMode ? (
                  <>
                    <button
                      onClick={() => setSelectedCompany(null)}
                      className="flex items-center space-x-2 px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
                    >
                      <X className="w-4 h-4" />
                      <span>Închide</span>
                    </button>
                    <button
                      onClick={() => setEditMode(true)}
                      className="flex items-center space-x-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
                    >
                      <Edit className="w-4 h-4" />
                      <span>Editează</span>
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={handleSaveOverrides}
                      disabled={saveLoading}
                      className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                      data-testid="admin-company-save-button"
                    >
                      <Save className="w-4 h-4" />
                      <span>{saveLoading ? 'Salvare...' : 'Salvează'}</span>
                    </button>
                    <button
                      onClick={() => {
                        setEditMode(false);
                        loadCompanyDetails(selectedCompany.cui);
                      }}
                      className="flex items-center space-x-2 px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
                    >
                      <X className="w-4 h-4" />
                      <span>Anulează</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="p-6 max-h-[500px] overflow-y-auto">
            <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-900">
                <strong>Notă:</strong> Modificările se salvează ca override-uri și NU modifică datele originale din baza de date.
              </div>
            </div>

            {selectedCompany && Object.entries(selectedCompany).map(([key, value]) => {
              if (key === '_id') return null;
              return renderFieldEditor(key, value);
            })}
          </div>
        </div>
      )}
    </AdminLayout>
  );
};

export default AdminCompaniesPage;
