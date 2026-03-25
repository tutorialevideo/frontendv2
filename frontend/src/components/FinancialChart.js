import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, DollarSign, Users } from 'lucide-react';

const FinancialChart = ({ cui }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeMetric, setActiveMetric] = useState('cifra_afaceri');

  useEffect(() => {
    loadFinancialData();
  }, [cui]);

  const loadFinancialData = async () => {
    try {
      const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const res = await fetch(`${API_URL}/api/company/${cui}/financials`);
      
      if (res.ok) {
        const result = await res.json();
        setData(result.data || []);
      }
    } catch (error) {
      console.error('Failed to load financial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    if (!value) return '0';
    return new Intl.NumberFormat('ro-RO', {
      style: 'decimal',
      maximumFractionDigits: 0
    }).format(value);
  };

  const formatTooltipValue = (value, name) => {
    if (name === 'numar_angajati') {
      return [value, 'Angajați'];
    }
    return [`${formatCurrency(value)} RON`, name === 'cifra_afaceri' ? 'Cifră de afaceri' : 'Profit net'];
  };

  const metrics = [
    { id: 'cifra_afaceri', label: 'Cifră de afaceri', icon: DollarSign, color: '#3b82f6' },
    { id: 'profit_net', label: 'Profit net', icon: TrendingUp, color: '#10b981' },
    { id: 'numar_angajati', label: 'Angajați', icon: Users, color: '#f59e0b' },
  ];

  if (loading) {
    return (
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-secondary rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-secondary rounded"></div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return null;
  }

  return (
    <div className="bg-card border border-border rounded-xl p-6" data-testid="financial-chart">
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-4">Evoluție date financiare</h3>
        
        {/* Metric Selector */}
        <div className="flex flex-wrap gap-2">
          {metrics.map((metric) => {
            const Icon = metric.icon;
            return (
              <button
                key={metric.id}
                onClick={() => setActiveMetric(metric.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors ${
                  activeMetric === metric.id
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-background border-border hover:bg-accent'
                }`}
                data-testid={`metric-button-${metric.id}`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm font-medium">{metric.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        {activeMetric === 'numar_angajati' ? (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="year" 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <Tooltip 
              formatter={formatTooltipValue}
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
            />
            <Bar 
              dataKey={activeMetric} 
              fill={metrics.find(m => m.id === activeMetric)?.color}
              radius={[8, 8, 0, 0]}
            />
          </BarChart>
        ) : (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="year" 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              tickFormatter={(value) => `${formatCurrency(value / 1000)}k`}
            />
            <Tooltip 
              formatter={formatTooltipValue}
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
            />
            <Line 
              type="monotone" 
              dataKey={activeMetric} 
              stroke={metrics.find(m => m.id === activeMetric)?.color}
              strokeWidth={3}
              dot={{ fill: metrics.find(m => m.id === activeMetric)?.color, r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        )}
      </ResponsiveContainer>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-border">
        {data.length > 0 && (
          <>
            <div className="text-center">
              <div className="text-sm text-muted-foreground mb-1">Primii ani</div>
              <div className="text-xl font-semibold">
                {activeMetric === 'numar_angajati' 
                  ? data[0][activeMetric] || 0
                  : `${formatCurrency(data[0][activeMetric])} RON`}
              </div>
              <div className="text-xs text-muted-foreground">{data[0].year}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-muted-foreground mb-1">Ultimul an</div>
              <div className="text-xl font-semibold">
                {activeMetric === 'numar_angajati'
                  ? data[data.length - 1][activeMetric] || 0
                  : `${formatCurrency(data[data.length - 1][activeMetric])} RON`}
              </div>
              <div className="text-xs text-muted-foreground">{data[data.length - 1].year}</div>
            </div>
            <div className="text-center">
              <div className="text-sm text-muted-foreground mb-1">Creștere</div>
              <div className={`text-xl font-semibold ${
                ((data[data.length - 1][activeMetric] || 0) - (data[0][activeMetric] || 0)) >= 0
                  ? 'text-green-600'
                  : 'text-red-600'
              }`}>
                {(() => {
                  const first = data[0][activeMetric] || 0;
                  const last = data[data.length - 1][activeMetric] || 0;
                  const growth = first > 0 ? ((last - first) / first * 100) : 0;
                  return `${growth >= 0 ? '+' : ''}${growth.toFixed(1)}%`;
                })()}
              </div>
              <div className="text-xs text-muted-foreground">Total</div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default FinancialChart;
