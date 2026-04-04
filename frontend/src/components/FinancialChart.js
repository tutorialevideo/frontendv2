import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, TrendingDown, Building2, Wallet, Landmark, CreditCard, PiggyBank, Banknote, Loader2 } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

const formatCurrency = (value) => {
  if (value === null || value === undefined) return '-';
  const abs = Math.abs(value);
  if (abs >= 1000000) return `${(value / 1000000).toFixed(1)}M RON`;
  if (abs >= 1000) return `${(value / 1000).toFixed(0)}K RON`;
  return `${value.toFixed(0)} RON`;
};

const formatFullCurrency = (value) => {
  if (value === null || value === undefined) return '-';
  return `${Math.round(value).toLocaleString('ro-RO')} RON`;
};

const BilanCard = ({ label, value, icon: Icon, color, trend }) => {
  const isNegative = value !== null && value !== undefined && value < 0;
  
  return (
    <div className={`border rounded-xl p-4 ${color}`} data-testid={`bilan-card-${label.toLowerCase().replace(/\s/g, '-')}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium opacity-80">{label}</span>
        <Icon className="w-4 h-4 opacity-60" />
      </div>
      <div className={`text-xl font-bold ${isNegative ? 'text-red-600' : ''}`}>
        {formatCurrency(value)}
      </div>
      {trend !== null && trend !== undefined && (
        <div className={`flex items-center gap-1 text-xs mt-1 ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
          <span>{trend >= 0 ? '+' : ''}{trend.toFixed(1)}% vs anul anterior</span>
        </div>
      )}
    </div>
  );
};

const FinancialChart = ({ cui }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${API_URL}/api/company/${cui}/financials`);
        const text = await response.text();
        let result = null;
        try { result = JSON.parse(text); } catch(e) {}
        if (result && result.data && result.data.length > 0) {
          setData(result.data);
        }
      } catch (err) {
        console.error('Error fetching financials:', err);
      } finally {
        setLoading(false);
      }
    };
    if (cui) fetchData();
  }, [cui]);

  if (loading) {
    return (
      <div className="bg-card border border-border rounded-xl p-6 flex items-center justify-center h-32">
        <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return null;
  }

  // Get latest year data and calculate trends
  const latest = data[data.length - 1];
  const prev = data.length > 1 ? data[data.length - 2] : null;

  const calcTrend = (field) => {
    if (!prev || !prev[field] || !latest[field] || prev[field] === 0) return null;
    return ((latest[field] - prev[field]) / Math.abs(prev[field])) * 100;
  };

  // Determine which fields are available
  const hasBalanceSheet = latest.active_imobilizate !== null || latest.active_circulante !== null || latest.datorii !== null;
  const hasIncomeStatement = latest.cifra_afaceri !== null || latest.profit_net !== null;

  // Build chart data
  const chartData = data.map(item => ({
    year: item.year,
    'Active imobilizate': item.active_imobilizate || 0,
    'Active circulante': item.active_circulante || 0,
    'Datorii': item.datorii || 0,
    'Capitaluri proprii': item.capitaluri_proprii || 0,
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload) return null;
    return (
      <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
        <p className="font-medium mb-1">Anul {label}</p>
        {payload.map((entry, i) => (
          <p key={i} className="text-xs" style={{ color: entry.color }}>
            {entry.name}: {formatFullCurrency(entry.value)}
          </p>
        ))}
      </div>
    );
  };

  return (
    <div className="bg-card border border-border rounded-xl p-6" data-testid="financial-chart">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary" />
          Bilanț contabil
        </h3>
        <span className="text-xs text-muted-foreground bg-secondary px-2 py-1 rounded">
          {data[0]?.year} - {data[data.length - 1]?.year}
        </span>
      </div>

      {/* KPI Cards - Latest Year */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-6">
        {hasIncomeStatement && latest.cifra_afaceri != null && (
          <BilanCard
            label="Cifra de afaceri"
            value={latest.cifra_afaceri}
            icon={Banknote}
            color="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800"
            trend={calcTrend('cifra_afaceri')}
          />
        )}
        {hasIncomeStatement && latest.profit_net != null && (
          <BilanCard
            label="Profit net"
            value={latest.profit_net}
            icon={TrendingUp}
            color={latest.profit_net >= 0
              ? "bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800"
              : "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800"}
            trend={calcTrend('profit_net')}
          />
        )}
        {hasBalanceSheet && (
          <>
            <BilanCard
              label="Active imobilizate"
              value={latest.active_imobilizate}
              icon={Building2}
              color="bg-indigo-50 dark:bg-indigo-950/30 border-indigo-200 dark:border-indigo-800"
              trend={calcTrend('active_imobilizate')}
            />
            <BilanCard
              label="Active circulante"
              value={latest.active_circulante}
              icon={Wallet}
              color="bg-sky-50 dark:bg-sky-950/30 border-sky-200 dark:border-sky-800"
              trend={calcTrend('active_circulante')}
            />
            <BilanCard
              label="Datorii totale"
              value={latest.datorii}
              icon={CreditCard}
              color="bg-orange-50 dark:bg-orange-950/30 border-orange-200 dark:border-orange-800"
              trend={calcTrend('datorii')}
            />
            <BilanCard
              label="Capitaluri proprii"
              value={latest.capitaluri_proprii}
              icon={Landmark}
              color={latest.capitaluri_proprii >= 0
                ? "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800"
                : "bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800"}
              trend={calcTrend('capitaluri_proprii')}
            />
            {latest.casa_conturi_banci != null && (
              <BilanCard
                label="Casa și conturi"
                value={latest.casa_conturi_banci}
                icon={PiggyBank}
                color="bg-teal-50 dark:bg-teal-950/30 border-teal-200 dark:border-teal-800"
                trend={calcTrend('casa_conturi_banci')}
              />
            )}
            {latest.capital_subscris != null && (
              <BilanCard
                label="Capital subscris"
                value={latest.capital_subscris}
                icon={Banknote}
                color="bg-purple-50 dark:bg-purple-950/30 border-purple-200 dark:border-purple-800"
                trend={null}
              />
            )}
          </>
        )}
        {latest.numar_angajati != null && (
          <BilanCard
            label="Angajați"
            value={latest.numar_angajati}
            icon={Building2}
            color="bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800"
            trend={calcTrend('numar_angajati')}
          />
        )}
      </div>

      {/* Bar Chart - Balance Sheet Comparison */}
      {hasBalanceSheet && data.length > 1 && (
        <div className="mb-6">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="year" stroke="#6b7280" style={{ fontSize: '12px' }} />
              <YAxis stroke="#6b7280" style={{ fontSize: '11px' }} tickFormatter={(v) => formatCurrency(v).replace(' RON', '')} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Bar dataKey="Active imobilizate" fill="#6366f1" radius={[2, 2, 0, 0]} />
              <Bar dataKey="Active circulante" fill="#0ea5e9" radius={[2, 2, 0, 0]} />
              <Bar dataKey="Datorii" fill="#f97316" radius={[2, 2, 0, 0]} />
              <Bar dataKey="Capitaluri proprii" fill="#10b981" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Detailed Year-by-Year Table */}
      <div className="overflow-x-auto border border-border rounded-lg">
        <table className="w-full text-sm" data-testid="bilant-table">
          <thead>
            <tr className="bg-secondary/50">
              <th className="text-left py-3 px-3 font-medium text-muted-foreground border-b border-border">An</th>
              {hasIncomeStatement && latest.cifra_afaceri != null && (
                <th className="text-right py-3 px-3 font-medium text-muted-foreground border-b border-border">Cifra afaceri</th>
              )}
              {hasIncomeStatement && latest.profit_net != null && (
                <th className="text-right py-3 px-3 font-medium text-muted-foreground border-b border-border">Profit net</th>
              )}
              {hasBalanceSheet && (
                <>
                  <th className="text-right py-3 px-3 font-medium text-muted-foreground border-b border-border">Active imob.</th>
                  <th className="text-right py-3 px-3 font-medium text-muted-foreground border-b border-border">Active circ.</th>
                  <th className="text-right py-3 px-3 font-medium text-muted-foreground border-b border-border">Datorii</th>
                  <th className="text-right py-3 px-3 font-medium text-muted-foreground border-b border-border">Capital propriu</th>
                </>
              )}
              {latest.numar_angajati != null && (
                <th className="text-right py-3 px-3 font-medium text-muted-foreground border-b border-border">Angajați</th>
              )}
            </tr>
          </thead>
          <tbody>
            {data.slice().reverse().map((item, index) => (
              <tr key={item.year} className={`border-b border-border/50 hover:bg-secondary/30 transition-colors ${index === 0 ? 'bg-primary/5 font-medium' : ''}`}>
                <td className="py-2.5 px-3 font-medium">{item.year}</td>
                {hasIncomeStatement && latest.cifra_afaceri != null && (
                  <td className="text-right py-2.5 px-3">{formatFullCurrency(item.cifra_afaceri)}</td>
                )}
                {hasIncomeStatement && latest.profit_net != null && (
                  <td className={`text-right py-2.5 px-3 ${item.profit_net >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatFullCurrency(item.profit_net)}
                  </td>
                )}
                {hasBalanceSheet && (
                  <>
                    <td className="text-right py-2.5 px-3">{formatFullCurrency(item.active_imobilizate)}</td>
                    <td className="text-right py-2.5 px-3">{formatFullCurrency(item.active_circulante)}</td>
                    <td className="text-right py-2.5 px-3 text-orange-600">{formatFullCurrency(item.datorii)}</td>
                    <td className={`text-right py-2.5 px-3 ${item.capitaluri_proprii >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                      {formatFullCurrency(item.capitaluri_proprii)}
                    </td>
                  </>
                )}
                {latest.numar_angajati != null && (
                  <td className="text-right py-2.5 px-3">{item.numar_angajati || '-'}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Data Source Info */}
      <div className="mt-4 p-3 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-900 rounded-lg">
        <p className="text-xs text-green-800 dark:text-green-200">
          <strong>Date oficiale</strong> din bilanțurile publicate la Ministerul Finanțelor ({data[0]?.year} - {data[data.length - 1]?.year}).
        </p>
      </div>
    </div>
  );
};

export default FinancialChart;
