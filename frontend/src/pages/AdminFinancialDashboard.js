import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, 
  TrendingDown,
  Building2, 
  Users, 
  DollarSign,
  BarChart3,
  PieChart,
  MapPin,
  Factory,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import AdminLayout from '../components/AdminLayout';

const AdminFinancialDashboard = () => {
  const { token } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/financial/admin/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const text = await response.text();
      
      if (response.ok && text) {
        const data = JSON.parse(text);
        setDashboard(data);
        setError(null);
      } else {
        const errorData = text ? JSON.parse(text) : {};
        setError(errorData.detail || 'Eroare la încărcarea dashboard-ului');
      }
    } catch (err) {
      setError('Eroare de rețea: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [token, API_URL]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const formatCurrency = (value) => {
    if (!value) return '0';
    if (value >= 1e9) return `${(value / 1e9).toFixed(2)} mld RON`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(2)} mil RON`;
    return `${value.toLocaleString('ro-RO')} RON`;
  };

  const formatNumber = (value) => {
    if (!value) return '0';
    return value.toLocaleString('ro-RO');
  };

  // CAEN sector names
  const caenSectors = {
    '01': 'Agricultură',
    '02': 'Silvicultură',
    '03': 'Pescuit',
    '05': 'Minerit cărbune',
    '06': 'Extracție petrol',
    '10': 'Industria alimentară',
    '13': 'Textile',
    '14': 'Confecții',
    '16': 'Prelucrare lemn',
    '20': 'Industria chimică',
    '22': 'Produse plastic',
    '23': 'Minerale nemetalice',
    '24': 'Metalurgie',
    '25': 'Produse metalice',
    '26': 'Calculatoare, electronice',
    '27': 'Echipamente electrice',
    '28': 'Mașini, utilaje',
    '29': 'Autovehicule',
    '31': 'Mobilă',
    '35': 'Energie, gaze',
    '36': 'Apă',
    '41': 'Construcții clădiri',
    '42': 'Inginerie civilă',
    '43': 'Construcții specializate',
    '45': 'Comerț auto',
    '46': 'Comerț en-gros',
    '47': 'Comerț en-detail',
    '49': 'Transport terestru',
    '50': 'Transport naval',
    '51': 'Transport aerian',
    '52': 'Depozitare',
    '53': 'Poștă, curierat',
    '55': 'Hoteluri',
    '56': 'Restaurante',
    '58': 'Edituri',
    '59': 'Film, TV',
    '61': 'Telecomunicații',
    '62': 'IT - Software',
    '63': 'IT - Servicii informații',
    '64': 'Servicii financiare',
    '65': 'Asigurări',
    '66': 'Activități auxiliare financiare',
    '68': 'Imobiliare',
    '69': 'Juridice, contabilitate',
    '70': 'Consultanță management',
    '71': 'Arhitectură, inginerie',
    '72': 'Cercetare-dezvoltare',
    '73': 'Publicitate',
    '74': 'Alte activități profesionale',
    '77': 'Închirieri',
    '78': 'Resurse umane',
    '79': 'Turism',
    '80': 'Securitate',
    '81': 'Servicii clădiri',
    '82': 'Servicii administrative',
    '85': 'Învățământ',
    '86': 'Sănătate',
    '87': 'Asistență socială rezidențială',
    '88': 'Asistență socială',
    '90': 'Artă, spectacole',
    '91': 'Biblioteci, muzee',
    '93': 'Sport, recreere',
    '94': 'Organizații',
    '95': 'Reparații bunuri',
    '96': 'Alte servicii personale'
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

  if (error) {
    return (
      <AdminLayout>
        <div className="p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-600 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      </AdminLayout>
    );
  }

  const { overall, top_industries, top_counties } = dashboard || {};

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Dashboard Financiar</h2>
            <p className="text-muted-foreground">
              Statistici agregate din baza de date ({formatNumber(overall?.total_firme_cu_date_financiare)} firme cu date financiare)
            </p>
          </div>
          <button
            onClick={fetchDashboard}
            className="flex items-center gap-2 px-4 py-2 bg-secondary rounded-lg hover:bg-secondary/80"
          >
            <RefreshCw className="w-4 h-4" />
            Actualizează
          </button>
        </div>

        {/* Overall Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white">
            <div className="flex items-center gap-2 opacity-80 text-sm">
              <Building2 className="w-4 h-4" />
              Firme cu date financiare
            </div>
            <div className="mt-2 text-3xl font-bold">
              {formatNumber(overall?.total_firme_cu_date_financiare)}
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-5 text-white">
            <div className="flex items-center gap-2 opacity-80 text-sm">
              <DollarSign className="w-4 h-4" />
              Total Cifră Afaceri
            </div>
            <div className="mt-2 text-3xl font-bold">
              {formatCurrency(overall?.total_cifra_afaceri)}
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-5 text-white">
            <div className="flex items-center gap-2 opacity-80 text-sm">
              <TrendingUp className="w-4 h-4" />
              Total Profit
            </div>
            <div className="mt-2 text-3xl font-bold">
              {formatCurrency(overall?.total_profit)}
            </div>
          </div>

          <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-5 text-white">
            <div className="flex items-center gap-2 opacity-80 text-sm">
              <Users className="w-4 h-4" />
              Total Angajați
            </div>
            <div className="mt-2 text-3xl font-bold">
              {formatNumber(overall?.total_angajati)}
            </div>
          </div>
        </div>

        {/* Profitability Stats */}
        <div className="grid md:grid-cols-2 gap-4">
          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-500" />
              Firme Profitabile
            </h3>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-green-600">
                  {formatNumber(overall?.firme_profitabile)}
                </div>
                <div className="text-sm text-muted-foreground">
                  {overall?.rata_profitabilitate?.toFixed(1)}% din total
                </div>
              </div>
              <div className="w-24 h-24 relative">
                <svg className="transform -rotate-90 w-24 h-24">
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    className="text-gray-200"
                  />
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    strokeDasharray={`${(overall?.rata_profitabilitate || 0) * 2.51} 251`}
                    className="text-green-500"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center text-lg font-bold">
                  {overall?.rata_profitabilitate?.toFixed(0)}%
                </div>
              </div>
            </div>
          </div>

          <div className="bg-card border border-border rounded-xl p-5">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <TrendingDown className="w-5 h-5 text-red-500" />
              Firme în Pierdere
            </h3>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-3xl font-bold text-red-600">
                  {formatNumber(overall?.firme_in_pierdere)}
                </div>
                <div className="text-sm text-muted-foreground">
                  {(100 - (overall?.rata_profitabilitate || 0)).toFixed(1)}% din total
                </div>
              </div>
              <div className="w-24 h-24 relative">
                <svg className="transform -rotate-90 w-24 h-24">
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    className="text-gray-200"
                  />
                  <circle
                    cx="48"
                    cy="48"
                    r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    strokeDasharray={`${(100 - (overall?.rata_profitabilitate || 0)) * 2.51} 251`}
                    className="text-red-500"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center text-lg font-bold">
                  {(100 - (overall?.rata_profitabilitate || 0)).toFixed(0)}%
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Top Industries */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Factory className="w-5 h-5 text-primary" />
            Top 10 Industrii după Cifra de Afaceri
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left text-sm text-muted-foreground border-b border-border">
                  <th className="pb-3 pr-4">Sector CAEN</th>
                  <th className="pb-3 pr-4 text-right">Firme</th>
                  <th className="pb-3 pr-4 text-right">Cifră Afaceri</th>
                  <th className="pb-3 pr-4 text-right">Angajați</th>
                  <th className="pb-3 text-right">Marja Profit</th>
                </tr>
              </thead>
              <tbody>
                {top_industries?.map((ind, index) => (
                  <tr key={ind.sector_caen} className="border-b border-border last:border-0">
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-xs flex items-center justify-center font-medium">
                          {index + 1}
                        </span>
                        <div>
                          <div className="font-medium">{caenSectors[ind.sector_caen] || `Sector ${ind.sector_caen}`}</div>
                          <div className="text-xs text-muted-foreground">CAEN {ind.sector_caen}xx</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-right font-medium">
                      {formatNumber(ind.total_firme)}
                    </td>
                    <td className="py-3 pr-4 text-right font-medium">
                      {formatCurrency(ind.total_cifra_afaceri)}
                    </td>
                    <td className="py-3 pr-4 text-right">
                      {formatNumber(ind.total_angajati)}
                    </td>
                    <td className="py-3 text-right">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        ind.marja_profit_medie > 10 
                          ? 'bg-green-100 text-green-700' 
                          : ind.marja_profit_medie > 0 
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-red-100 text-red-700'
                      }`}>
                        {ind.marja_profit_medie?.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Counties */}
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-primary" />
            Top 10 Județe după Cifra de Afaceri
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            {top_counties?.map((county, index) => {
              const maxCA = top_counties[0]?.total_cifra_afaceri || 1;
              const percentage = (county.total_cifra_afaceri / maxCA) * 100;
              
              return (
                <div key={county.judet} className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-primary/10 text-primary text-xs flex items-center justify-center font-medium shrink-0">
                    {index + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium truncate">{county.judet}</span>
                      <span className="text-sm text-muted-foreground">
                        {formatNumber(county.total_firme)} firme
                      </span>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <div className="text-xs text-muted-foreground mt-1">
                      {formatCurrency(county.total_cifra_afaceri)}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="text-sm text-muted-foreground text-center">
          Date generate la: {dashboard?.generated_at ? new Date(dashboard.generated_at).toLocaleString('ro-RO') : 'N/A'}
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminFinancialDashboard;
