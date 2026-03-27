import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, 
  FileText, 
  Globe, 
  Save,
  RotateCcw,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Code
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import AdminLayout from '../components/AdminLayout';

const PAGE_TYPE_LABELS = {
  company: 'Pagină Firmă',
  search: 'Pagină Căutare',
  caen_category: 'Categorie CAEN',
  homepage: 'Pagina Principală',
  judet: 'Pagină Județ',
  localitate: 'Pagină Localitate'
};

const PAGE_TYPE_ICONS = {
  company: FileText,
  search: Search,
  caen_category: Code,
  homepage: Globe,
  judet: Globe,
  localitate: Globe
};

const SAMPLE_DATA = {
  company: {
    DENUMIRE: 'SC EXEMPLU SRL',
    CUI: '12345678',
    LOCALITATE: 'București',
    JUDET: 'București',
    CAEN: '6201',
    CAEN_DESCRIERE: 'Activități de realizare a soft-ului la comandă',
    AN: '2024',
    CIFRA_AFACERI: '1.500.000 RON',
    PROFIT: '250.000 RON'
  },
  search: {
    QUERY: 'restaurant bucuresti'
  },
  caen_category: {
    CAEN: '6201',
    CAEN_DESCRIERE: 'Activități de realizare a soft-ului la comandă'
  },
  homepage: {},
  judet: {
    JUDET: 'Cluj'
  },
  localitate: {
    LOCALITATE: 'Cluj-Napoca',
    JUDET: 'Cluj'
  }
};

const AdminSeoPage = () => {
  const { token } = useAuth();
  const [templates, setTemplates] = useState({});
  const [variables, setVariables] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState({});
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [expandedSections, setExpandedSections] = useState({});
  const [previews, setPreviews] = useState({});

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  const fetchTemplates = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/seo/admin/templates`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (response.ok) {
        setTemplates(data.templates || {});
        setVariables(data.variables || []);
        
        // Expand first section by default
        if (data.templates && Object.keys(data.templates).length > 0) {
          setExpandedSections({ [Object.keys(data.templates)[0]]: true });
        }
        
        // Generate initial previews
        const initialPreviews = {};
        Object.keys(data.templates || {}).forEach(pageType => {
          initialPreviews[pageType] = generatePreview(data.templates[pageType], pageType);
        });
        setPreviews(initialPreviews);
        
        setError(null);
      } else {
        setError(data.detail || 'Eroare la încărcarea template-urilor');
      }
    } catch (err) {
      setError('Eroare de rețea: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [token, API_URL]);

  useEffect(() => {
    fetchTemplates();
  }, [fetchTemplates]);

  const generatePreview = (template, pageType) => {
    if (!template) return { title: '', description: '' };
    
    const sampleData = SAMPLE_DATA[pageType] || {};
    
    let title = template.title_template || '';
    let description = template.description_template || '';
    
    Object.entries(sampleData).forEach(([key, value]) => {
      const regex = new RegExp(`\\{${key}\\}`, 'g');
      title = title.replace(regex, value);
      description = description.replace(regex, value);
    });
    
    return { title, description };
  };

  const handleTemplateChange = (pageType, field, value) => {
    setTemplates(prev => ({
      ...prev,
      [pageType]: {
        ...prev[pageType],
        [field]: value
      }
    }));
    
    // Update preview
    const updatedTemplate = {
      ...templates[pageType],
      [field]: value
    };
    setPreviews(prev => ({
      ...prev,
      [pageType]: generatePreview(updatedTemplate, pageType)
    }));
  };

  const saveTemplate = async (pageType) => {
    setSaving(prev => ({ ...prev, [pageType]: true }));
    setSuccess(null);
    
    try {
      const template = templates[pageType];
      
      const response = await fetch(`${API_URL}/api/seo/admin/template/${pageType}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title_template: template.title_template,
          description_template: template.description_template,
          index: template.index,
          enabled: template.enabled
        })
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (response.ok) {
        setSuccess(`Template "${PAGE_TYPE_LABELS[pageType]}" salvat cu succes!`);
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError(data.detail || 'Eroare la salvare');
      }
    } catch (err) {
      setError('Eroare de rețea: ' + err.message);
    } finally {
      setSaving(prev => ({ ...prev, [pageType]: false }));
    }
  };

  const resetTemplate = async (pageType) => {
    if (!window.confirm(`Resetezi template-ul "${PAGE_TYPE_LABELS[pageType]}" la valorile default?`)) {
      return;
    }
    
    setSaving(prev => ({ ...prev, [pageType]: true }));
    
    try {
      const response = await fetch(`${API_URL}/api/seo/admin/reset/${pageType}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const text = await response.text();
      const data = text ? JSON.parse(text) : {};
      
      if (response.ok) {
        setTemplates(prev => ({
          ...prev,
          [pageType]: data.template
        }));
        setPreviews(prev => ({
          ...prev,
          [pageType]: generatePreview(data.template, pageType)
        }));
        setSuccess(`Template "${PAGE_TYPE_LABELS[pageType]}" resetat!`);
        setTimeout(() => setSuccess(null), 3000);
      } else {
        setError(data.detail || 'Eroare la resetare');
      }
    } catch (err) {
      setError('Eroare de rețea: ' + err.message);
    } finally {
      setSaving(prev => ({ ...prev, [pageType]: false }));
    }
  };

  const toggleSection = (pageType) => {
    setExpandedSections(prev => ({
      ...prev,
      [pageType]: !prev[pageType]
    }));
  };

  const getVariablesForPageType = (pageType) => {
    return variables.filter(v => 
      v.applies_to.includes(pageType) || v.applies_to.includes('all')
    );
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h2 className="text-2xl font-bold">SEO Templates</h2>
          <p className="text-muted-foreground">
            Configurează titluri și descrieri dinamice pentru paginile site-ului
          </p>
        </div>

        {/* Alerts */}
        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-600 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}
        
        {success && (
          <div className="p-4 bg-green-500/10 border border-green-500/50 rounded-lg text-green-600 flex items-center gap-2">
            <CheckCircle className="w-5 h-5" />
            {success}
          </div>
        )}

        {/* Variables Reference */}
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-5 h-5 text-blue-500" />
            <h3 className="font-semibold">Variabile disponibile</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {variables.map(v => (
              <span 
                key={v.name}
                className="px-2 py-1 bg-blue-500/10 text-blue-600 rounded text-sm font-mono"
                title={v.description}
              >
                {`{${v.name}}`}
              </span>
            ))}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Folosește aceste variabile în template-uri. Vor fi înlocuite automat cu datele reale.
          </p>
        </div>

        {/* Templates */}
        <div className="space-y-4">
          {Object.entries(templates).map(([pageType, template]) => {
            const Icon = PAGE_TYPE_ICONS[pageType] || Globe;
            const isExpanded = expandedSections[pageType];
            const preview = previews[pageType] || {};
            const applicableVars = getVariablesForPageType(pageType);
            
            return (
              <div key={pageType} className="bg-card border border-border rounded-xl overflow-hidden">
                {/* Header */}
                <button
                  onClick={() => toggleSection(pageType)}
                  className="w-full px-6 py-4 flex items-center justify-between hover:bg-secondary/50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-5 h-5 text-primary" />
                    <span className="font-semibold">{PAGE_TYPE_LABELS[pageType]}</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      template.index 
                        ? 'bg-green-500/10 text-green-600' 
                        : 'bg-red-500/10 text-red-600'
                    }`}>
                      {template.index ? 'index' : 'noindex'}
                    </span>
                  </div>
                  {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </button>

                {/* Content */}
                {isExpanded && (
                  <div className="px-6 pb-6 space-y-4 border-t border-border pt-4">
                    {/* Index Toggle */}
                    <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                      <div className="flex items-center gap-2">
                        {template.index ? (
                          <Eye className="w-4 h-4 text-green-600" />
                        ) : (
                          <EyeOff className="w-4 h-4 text-red-600" />
                        )}
                        <span className="text-sm">Indexare Google</span>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={template.index}
                          onChange={(e) => handleTemplateChange(pageType, 'index', e.target.checked)}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-500"></div>
                      </label>
                    </div>

                    {/* Applicable Variables */}
                    <div className="flex flex-wrap gap-1">
                      <span className="text-xs text-muted-foreground mr-2">Variabile pentru această pagină:</span>
                      {applicableVars.map(v => (
                        <code 
                          key={v.name}
                          className="px-1.5 py-0.5 bg-secondary text-xs rounded cursor-help"
                          title={v.description}
                        >
                          {`{${v.name}}`}
                        </code>
                      ))}
                    </div>

                    {/* Title Template */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Title Template
                      </label>
                      <input
                        type="text"
                        value={template.title_template || ''}
                        onChange={(e) => handleTemplateChange(pageType, 'title_template', e.target.value)}
                        className="w-full px-4 py-2 bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                        placeholder="Titlul paginii..."
                      />
                      {preview.title && (
                        <div className="mt-2 p-2 bg-blue-500/5 rounded border border-blue-500/20">
                          <span className="text-xs text-muted-foreground">Preview:</span>
                          <p className="text-sm text-blue-600 font-medium">{preview.title}</p>
                        </div>
                      )}
                    </div>

                    {/* Description Template */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Meta Description Template
                      </label>
                      <textarea
                        value={template.description_template || ''}
                        onChange={(e) => handleTemplateChange(pageType, 'description_template', e.target.value)}
                        rows={3}
                        className="w-full px-4 py-2 bg-secondary border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm resize-none"
                        placeholder="Descrierea paginii..."
                      />
                      {preview.description && (
                        <div className="mt-2 p-2 bg-blue-500/5 rounded border border-blue-500/20">
                          <span className="text-xs text-muted-foreground">Preview:</span>
                          <p className="text-sm text-blue-600">{preview.description}</p>
                        </div>
                      )}
                      <p className="text-xs text-muted-foreground mt-1">
                        Recomandat: 150-160 caractere. Actual: {(template.description_template || '').length}
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-3 pt-2">
                      <button
                        onClick={() => saveTemplate(pageType)}
                        disabled={saving[pageType]}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50"
                      >
                        {saving[pageType] ? (
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        ) : (
                          <Save className="w-4 h-4" />
                        )}
                        Salvează
                      </button>
                      <button
                        onClick={() => resetTemplate(pageType)}
                        disabled={saving[pageType]}
                        className="flex items-center gap-2 px-4 py-2 bg-secondary text-foreground rounded-lg hover:bg-secondary/80 disabled:opacity-50"
                      >
                        <RotateCcw className="w-4 h-4" />
                        Reset Default
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminSeoPage;
