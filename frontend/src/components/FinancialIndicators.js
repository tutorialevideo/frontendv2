import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown,
  DollarSign, 
  Percent, 
  Activity,
  Shield,
  Users,
  BarChart3,
  Download,
  ChevronDown,
  ChevronUp,
  Info,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';

const FinancialIndicators = ({ cui }) => {
  const [indicators, setIndicators] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    profitability: true,
    liquidity: false,
    solvency: false,
    efficiency: false
  });

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    const fetchIndicators = async () => {
      if (!cui) return;
      
      setLoading(true);
      try {
        const response = await fetch(`${API_URL}/api/financial/indicators/${cui}`);
        const text = await response.text();
        
        if (response.ok && text) {
          const data = JSON.parse(text);
          setIndicators(data);
          setError(null);
        } else {
          setError('Nu s-au putut încărca indicatorii financiari');
        }
      } catch (err) {
        setError('Eroare la încărcare: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchIndicators();
  }, [cui, API_URL]);

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getRatingColor = (rating) => {
    switch (rating) {
      case 'Excelent': return 'bg-green-100 text-green-700 border-green-300';
      case 'Bun': return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'Mediu': return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      case 'Slab': return 'bg-red-100 text-red-700 border-red-300';
      default: return 'bg-gray-100 text-gray-600 border-gray-300';
    }
  };

  const getHealthColor = (color) => {
    switch (color) {
      case 'green': return 'from-green-500 to-green-600';
      case 'blue': return 'from-blue-500 to-blue-600';
      case 'yellow': return 'from-yellow-500 to-yellow-600';
      case 'red': return 'from-red-500 to-red-600';
      default: return 'from-gray-500 to-gray-600';
    }
  };

  const getHealthIcon = (status) => {
    switch (status) {
      case 'Excelentă': return <CheckCircle className="w-6 h-6" />;
      case 'Bună': return <CheckCircle className="w-6 h-6" />;
      case 'Medie': return <AlertTriangle className="w-6 h-6" />;
      case 'Slabă': return <XCircle className="w-6 h-6" />;
      default: return <Activity className="w-6 h-6" />;
    }
  };

  const downloadPDF = () => {
    window.open(`${API_URL}/api/financial/indicators/${cui}/pdf`, '_blank');
  };

  if (loading) {
    return (
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-3 text-muted-foreground">Se calculează indicatorii financiari...</span>
        </div>
      </div>
    );
  }

  if (error || !indicators) {
    return (
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Info className="w-5 h-5" />
          <span>Indicatorii financiari nu sunt disponibili pentru această firmă</span>
        </div>
      </div>
    );
  }

  const { raw_data, profitability, liquidity, solvency, efficiency, health_score } = indicators;

  const IndicatorRow = ({ label, data, showRating = true }) => (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <div className="flex-1">
        <div className="font-medium text-sm">{label}</div>
        <div className="text-xs text-muted-foreground">{data.description}</div>
      </div>
      <div className="flex items-center gap-3">
        <span className="font-semibold text-lg">{data.formatted}</span>
        {showRating && data.rating && data.rating !== 'N/A' && (
          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getRatingColor(data.rating)}`}>
            {data.rating}
          </span>
        )}
      </div>
    </div>
  );

  const SectionHeader = ({ title, icon: Icon, section, color }) => (
    <button
      onClick={() => toggleSection(section)}
      className={`w-full flex items-center justify-between p-4 rounded-lg transition-colors ${
        expandedSections[section] ? 'bg-secondary' : 'hover:bg-secondary/50'
      }`}
    >
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        <span className="font-semibold">{title}</span>
      </div>
      {expandedSections[section] ? (
        <ChevronUp className="w-5 h-5 text-muted-foreground" />
      ) : (
        <ChevronDown className="w-5 h-5 text-muted-foreground" />
      )}
    </button>
  );

  return (
    <div className="space-y-6" data-testid="financial-indicators">
      {/* Health Score Card */}
      <div className={`relative overflow-hidden rounded-xl bg-gradient-to-r ${getHealthColor(health_score.color)} p-6 text-white`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium opacity-90">Scor Sănătate Financiară</h3>
            <div className="flex items-center gap-3 mt-2">
              {getHealthIcon(health_score.status)}
              <span className="text-4xl font-bold">{health_score.score}/100</span>
            </div>
            <p className="mt-2 text-lg font-medium">{health_score.status}</p>
          </div>
          <button
            onClick={downloadPDF}
            className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
          >
            <Download className="w-5 h-5" />
            <span>Descarcă Raport</span>
          </button>
        </div>
        
        {/* Progress bar */}
        <div className="mt-4 h-2 bg-white/20 rounded-full overflow-hidden">
          <div 
            className="h-full bg-white rounded-full transition-all duration-1000"
            style={{ width: `${health_score.score}%` }}
          />
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <DollarSign className="w-4 h-4" />
            Cifra de afaceri
          </div>
          <div className="mt-1 text-xl font-bold">
            {raw_data.cifra_afaceri?.toLocaleString('ro-RO')} RON
          </div>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            {raw_data.profit_net >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-500" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-500" />
            )}
            Profit net
          </div>
          <div className={`mt-1 text-xl font-bold ${raw_data.profit_net >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {raw_data.profit_net?.toLocaleString('ro-RO')} RON
          </div>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <BarChart3 className="w-4 h-4" />
            Total active
          </div>
          <div className="mt-1 text-xl font-bold">
            {raw_data.total_active?.toLocaleString('ro-RO')} RON
          </div>
        </div>
        <div className="bg-card border border-border rounded-xl p-4">
          <div className="flex items-center gap-2 text-muted-foreground text-sm">
            <Shield className="w-4 h-4" />
            Capitaluri proprii
          </div>
          <div className={`mt-1 text-xl font-bold ${raw_data.capitaluri_proprii >= 0 ? '' : 'text-red-600'}`}>
            {raw_data.capitaluri_proprii?.toLocaleString('ro-RO')} RON
          </div>
        </div>
      </div>

      {/* Detailed Indicators */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        {/* Profitability */}
        <div className="border-b border-border">
          <SectionHeader 
            title="Indicatori de Profitabilitate" 
            icon={TrendingUp} 
            section="profitability"
            color="bg-green-500"
          />
          {expandedSections.profitability && (
            <div className="p-4 space-y-1">
              <IndicatorRow label="Marja Profit Brut" data={profitability.marja_profit_brut} />
              <IndicatorRow label="Marja Profit Net" data={profitability.marja_profit_net} />
              <IndicatorRow label="ROA (Return on Assets)" data={profitability.roa} />
              <IndicatorRow label="ROE (Return on Equity)" data={profitability.roe} />
              <IndicatorRow label="Rentabilitate Economică" data={profitability.rata_rentabilitate_economica} />
            </div>
          )}
        </div>

        {/* Liquidity */}
        <div className="border-b border-border">
          <SectionHeader 
            title="Indicatori de Lichiditate" 
            icon={Activity} 
            section="liquidity"
            color="bg-blue-500"
          />
          {expandedSections.liquidity && (
            <div className="p-4 space-y-1">
              <IndicatorRow label="Lichiditate Curentă" data={liquidity.lichiditate_curenta} />
              <IndicatorRow label="Lichiditate Rapidă (Test Acid)" data={liquidity.lichiditate_rapida} />
              <IndicatorRow label="Lichiditate Imediată (Cash Ratio)" data={liquidity.lichiditate_imediata} />
            </div>
          )}
        </div>

        {/* Solvency */}
        <div className="border-b border-border">
          <SectionHeader 
            title="Indicatori de Solvabilitate" 
            icon={Shield} 
            section="solvency"
            color="bg-purple-500"
          />
          {expandedSections.solvency && (
            <div className="p-4 space-y-1">
              <IndicatorRow label="Rata Îndatorării" data={solvency.rata_indatorarii} />
              <IndicatorRow label="Autonomie Financiară" data={solvency.autonomie_financiara} />
              <IndicatorRow label="Levier Financiar" data={solvency.levier_financiar} />
              <IndicatorRow label="Solvabilitate Generală" data={solvency.solvabilitate_generala} />
            </div>
          )}
        </div>

        {/* Efficiency */}
        <div>
          <SectionHeader 
            title="Indicatori de Eficiență" 
            icon={Users} 
            section="efficiency"
            color="bg-orange-500"
          />
          {expandedSections.efficiency && (
            <div className="p-4 space-y-1">
              <IndicatorRow label="Productivitatea Muncii" data={efficiency.productivitate_munca} showRating={false} />
              <IndicatorRow label="Profit per Angajat" data={efficiency.profit_per_angajat} showRating={false} />
              <IndicatorRow label="Rata Cheltuielilor" data={efficiency.rata_cheltuieli} />
              <IndicatorRow label="Eficiența Activelor" data={efficiency.eficienta_activelor} showRating={false} />
            </div>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-sm">
        <span className="text-muted-foreground">Legendă rating:</span>
        <span className={`px-2 py-1 rounded-full border ${getRatingColor('Excelent')}`}>Excelent</span>
        <span className={`px-2 py-1 rounded-full border ${getRatingColor('Bun')}`}>Bun</span>
        <span className={`px-2 py-1 rounded-full border ${getRatingColor('Mediu')}`}>Mediu</span>
        <span className={`px-2 py-1 rounded-full border ${getRatingColor('Slab')}`}>Slab</span>
      </div>
    </div>
  );
};

export default FinancialIndicators;
