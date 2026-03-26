import React, { useState, useEffect, useCallback } from 'react';
import { Helmet } from 'react-helmet-async';
import { useAuth } from '../contexts/AuthContext';
import AdminLayout from '../components/AdminLayout';
import { 
  Search, 
  Edit, 
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
  MapPin,
  Phone,
  Mail,
  Calendar,
  Users,
  DollarSign,
  Briefcase,
  ArrowLeft,
  ExternalLink,
  Copy,
  Trash2
} from 'lucide-react';

const AdminCompaniesPage = () => {
  const { token } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [fullCompanyData, setFullCompanyData] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editedFields, setEditedFields] = useState({});
  const [loading, setLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showProfile, setShowProfile] = useState(false);

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

  const loadFullCompanyData = async (cui) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/companies/full/${cui}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setFullCompanyData(data);
        setSelectedCompany(data);
        setEditedFields({});
        setShowProfile(true);
      }
    } catch (error) {
      console.error('Failed to load company details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveChanges = async () => {
    if (!selectedCompany || Object.keys(editedFields).length === 0) return;

    setSaveLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/admin/companies/update/${selectedCompany.cui}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          overrides: editedFields,
          notes: 'Manual edit from admin panel'
        })
      });

      if (res.ok) {
        alert('Modificările au fost salvate cu succes!');
        setEditMode(false);
        loadFullCompanyData(selectedCompany.cui);
      } else {
        const data = await res.json();
        alert(data.detail || 'Eroare la salvare');
      }
    } catch (error) {
      console.error('Failed to save:', error);
      alert('Eroare la salvarea modificărilor');
    } finally {
      setSaveLoading(false);
    }
  };

  const handleFieldChange = (fieldName, value) => {
    setEditedFields(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copiat în clipboard!');
  };

  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  // Field categories for organization
  const fieldCategories = {
    'Identificare': ['cui', 'denumire', 'cod_inregistrare', 'euid'],
    'Locație': ['judet', 'localitate', 'strada', 'numar', 'bloc', 'scara', 'etaj', 'apartament', 'cod_postal'],
    'Contact': ['anaf_telefon', 'anaf_fax', 'email', 'website'],
    'Juridic': ['forma_juridica', 'anaf_forma_juridica', 'anaf_forma_organizare', 'anaf_forma_proprietate'],
    'ANAF': ['anaf_stare', 'anaf_data_inregistrare', 'anaf_cod_caen', 'anaf_platitor_tva', 'anaf_inactiv', 'anaf_stare_startswith_inregistrat'],
    'CAEN': ['caen_denumire', 'caen_sectiune', 'caen_sectiune_denumire'],
    'Financiar': ['mf_cifra_afaceri', 'mf_profit', 'mf_numar_angajati', 'mf_an_bilant', 'mf_platitor_tva'],
    'Alte date': []
  };

  const getFieldValue = (fieldName) => {
    if (editMode && fieldName in editedFields) {
      return editedFields[fieldName];
    }
    return fullCompanyData?.[fieldName];
  };

  const formatFieldValue = (value) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'boolean') return value ? 'Da' : 'Nu';
    if (typeof value === 'number') return value.toLocaleString('ro-RO');
    return String(value);
  };

  const renderField = (fieldName, value) => {
    const displayValue = getFieldValue(fieldName);
    const isEdited = fieldName in editedFields;

    return (
      <div key={fieldName} className="flex items-start justify-between py-2 border-b border-border last:border-0">
        <div className="flex-1">
          <label className="text-xs text-muted-foreground block mb-1">{fieldName}</label>
          {editMode ? (
            <input
              type="text"
              value={displayValue ?? ''}
              onChange={(e) => handleFieldChange(fieldName, e.target.value)}
              className={`w-full px-2 py-1 text-sm border rounded bg-background ${isEdited ? 'border-primary bg-primary/5' : 'border-border'}`}
            />
          ) : (
            <div className="flex items-center gap-2">
              <span className={`text-sm ${displayValue ? '' : 'text-muted-foreground'}`}>
                {formatFieldValue(displayValue)}
              </span>
              {displayValue && (
                <button
                  onClick={() => copyToClipboard(String(displayValue))}
                  className="p-1 hover:bg-muted rounded opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Copiază"
                >
                  <Copy className="w-3 h-3 text-muted-foreground" />
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  // Company Profile View
  if (showProfile) {
    // Show loading while data loads
    if (loading || !fullCompanyData) {
      return (
        <AdminLayout>
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
          </div>
        </AdminLayout>
      );
    }
    
    const usedFields = new Set(Object.values(fieldCategories).flat());
    const otherFields = Object.keys(fullCompanyData).filter(
      k => !usedFields.has(k) && k !== '_id' && k !== 'id'
    );
    fieldCategories['Alte date'] = otherFields;

    return (
      <AdminLayout>

        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => { setShowProfile(false); setSelectedCompany(null); setFullCompanyData(null); }}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Înapoi la listă
          </button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight mb-1">
                {fullCompanyData.denumire}
              </h1>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <span className="font-mono">CUI: {fullCompanyData.cui}</span>
                <span>•</span>
                <span>{fullCompanyData.judet}, {fullCompanyData.localitate}</span>
                {fullCompanyData.anaf_stare_startswith_inregistrat && (
                  <>
                    <span>•</span>
                    <span className="flex items-center gap-1 text-green-600">
                      <CheckCircle className="w-4 h-4" />
                      Activ ANAF
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              {editMode ? (
                <>
                  <button
                    onClick={handleSaveChanges}
                    disabled={saveLoading || Object.keys(editedFields).length === 0}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                  >
                    <Save className="w-4 h-4" />
                    {saveLoading ? 'Salvare...' : 'Salvează modificările'}
                    {Object.keys(editedFields).length > 0 && (
                      <span className="ml-1 px-1.5 py-0.5 bg-white/20 rounded text-xs">
                        {Object.keys(editedFields).length}
                      </span>
                    )}
                  </button>
                  <button
                    onClick={() => { setEditMode(false); setEditedFields({}); }}
                    className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-muted"
                  >
                    <X className="w-4 h-4" />
                    Anulează
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={() => setEditMode(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
                  >
                    <Edit className="w-4 h-4" />
                    Editează
                  </button>
                  <a
                    href={`/firma/${fullCompanyData.denumire?.toLowerCase().replace(/[^a-z0-9]/g, '-')}-${fullCompanyData.cui}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-muted"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Vezi public
                  </a>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Edit mode notice */}
        {editMode && (
          <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-amber-900">
              <strong>Mod editare activ.</strong> Modificările se salvează ca override-uri și vor fi vizibile pe profilul public al firmei.
              Câmpurile modificate sunt evidențiate cu albastru.
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <DollarSign className="w-4 h-4" />
              <span className="text-xs">Cifra de afaceri</span>
            </div>
            <div className="text-lg font-semibold">
              {fullCompanyData.mf_cifra_afaceri 
                ? `${Number(fullCompanyData.mf_cifra_afaceri).toLocaleString('ro-RO')} RON`
                : '-'
              }
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Activity className="w-4 h-4" />
              <span className="text-xs">Profit</span>
            </div>
            <div className="text-lg font-semibold">
              {fullCompanyData.mf_profit 
                ? `${Number(fullCompanyData.mf_profit).toLocaleString('ro-RO')} RON`
                : '-'
              }
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Users className="w-4 h-4" />
              <span className="text-xs">Angajați</span>
            </div>
            <div className="text-lg font-semibold">
              {fullCompanyData.mf_numar_angajati ?? '-'}
            </div>
          </div>
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="flex items-center gap-2 text-muted-foreground mb-1">
              <Briefcase className="w-4 h-4" />
              <span className="text-xs">Cod CAEN</span>
            </div>
            <div className="text-lg font-semibold font-mono">
              {fullCompanyData.anaf_cod_caen || '-'}
            </div>
            {fullCompanyData.caen_denumire && (
              <div className="text-xs text-muted-foreground mt-0.5">{fullCompanyData.caen_denumire}</div>
            )}
          </div>
        </div>

        {/* All Fields by Category */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(fieldCategories).map(([category, fields]) => {
            const categoryFields = fields.filter(f => fullCompanyData.hasOwnProperty(f) || editMode);
            if (categoryFields.length === 0 && !editMode) return null;

            return (
              <div key={category} className="bg-card border border-border rounded-xl overflow-hidden">
                <div className="px-4 py-3 bg-muted/50 border-b border-border">
                  <h3 className="font-semibold text-sm">{category}</h3>
                </div>
                <div className="p-4 space-y-1 group">
                  {fields.map(fieldName => {
                    if (!fullCompanyData.hasOwnProperty(fieldName) && !editMode) return null;
                    return renderField(fieldName, fullCompanyData[fieldName]);
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Raw JSON (collapsible) */}
        <details className="mt-6 bg-card border border-border rounded-xl">
          <summary className="px-4 py-3 cursor-pointer hover:bg-muted/50 font-medium text-sm">
            Date brute (JSON) - {Object.keys(fullCompanyData).length} câmpuri
          </summary>
          <pre className="p-4 text-xs overflow-x-auto bg-muted/30 max-h-96">
            {JSON.stringify(fullCompanyData, null, 2)}
          </pre>
        </details>
      </AdminLayout>
    );
  }

  // Companies List View
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

      {/* Search */}
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
            className="px-5 py-2.5 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 flex items-center gap-2"
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
                    ANAF
                  </span>
                </th>
                <th className="text-center px-4 py-3 text-sm font-semibold">
                  <span className="flex items-center justify-center gap-1">
                    <Receipt className="w-4 h-4" />
                    TVA
                  </span>
                </th>
                <th className="text-right px-4 py-3 text-sm font-semibold">CA (RON)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {loading && companies.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-4 py-12 text-center">
                    <RefreshCw className="w-8 h-8 mx-auto mb-3 animate-spin text-muted-foreground" />
                    <p className="text-muted-foreground">Se încarcă...</p>
                  </td>
                </tr>
              ) : companies.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-4 py-12 text-center">
                    <Building2 className="w-12 h-12 mx-auto mb-3 text-muted-foreground opacity-50" />
                    <p className="text-muted-foreground">Niciun rezultat găsit</p>
                  </td>
                </tr>
              ) : (
                companies.map((company) => (
                  <tr 
                    key={company.cui} 
                    className="hover:bg-muted/30 transition-colors cursor-pointer"
                    onClick={() => loadFullCompanyData(company.cui)}
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
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {company.anaf_stare_startswith_inregistrat ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                          <CheckCircle className="w-3 h-3" />
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                          <XCircle className="w-3 h-3" />
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {company.anaf_platitor_tva || company.mf_platitor_tva ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                          <CheckCircle className="w-3 h-3" />
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-500">
                          <XCircle className="w-3 h-3" />
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-sm">
                      {company.mf_cifra_afaceri 
                        ? Number(company.mf_cifra_afaceri).toLocaleString('ro-RO')
                        : '-'
                      }
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
                className="p-2 border border-border rounded-lg hover:bg-muted disabled:opacity-50"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              
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
                      className={`w-8 h-8 rounded-lg text-sm font-medium ${
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
                className="p-2 border border-border rounded-lg hover:bg-muted disabled:opacity-50"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
};

export default AdminCompaniesPage;
