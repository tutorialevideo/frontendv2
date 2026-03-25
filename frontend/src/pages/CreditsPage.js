import React, { useState, useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { useNavigate } from 'react-router-dom';
import { CreditCard, Sparkles, Zap, Check, ArrowLeft, Eye, Calendar } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useCredits } from '../contexts/CreditsContext';

const CreditsPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, token, loading: authLoading } = useAuth();
  const { creditsBalance, freeViewsToday, freeViewsMax, totalViews, systemEnabled, refreshCredits, loading: creditsLoading } = useCredits();
  const [packages, setPackages] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    // Wait for auth to load before redirecting
    if (authLoading) return;
    
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    fetchPackages();
  }, [isAuthenticated, authLoading, navigate]);

  const fetchPackages = async () => {
    try {
      const res = await fetch(`${API_URL}/api/credits/packages`);
      if (res.ok) {
        const data = await res.json();
        setPackages(data.packages);
      }
    } catch (error) {
      console.error('Failed to fetch packages:', error);
    }
  };

  const handlePurchase = async (packageId) => {
    if (!token) return;
    
    setLoading(true);
    setSelectedPackage(packageId);

    try {
      // In production, this would redirect to Stripe checkout
      // For now, we'll simulate a purchase
      const pkg = packages.find(p => p.id === packageId);
      
      // Call add credits endpoint (simulated - in production this comes from Stripe webhook)
      const res = await fetch(`${API_URL}/api/credits/add?credits_to_add=${pkg.credits}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (res.ok) {
        refreshCredits();
        alert(`Ai adăugat ${pkg.credits} credite cu succes!`);
      }
    } catch (error) {
      console.error('Purchase failed:', error);
      alert('Eroare la procesarea plății. Te rugăm să încerci din nou.');
    } finally {
      setLoading(false);
      setSelectedPackage(null);
    }
  };

  if (authLoading || creditsLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (!systemEnabled) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="text-center">
          <CreditCard className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50" />
          <h2 className="text-xl font-semibold mb-2">Sistemul de credite nu este activ</h2>
          <p className="text-muted-foreground">
            Accesul la firme este momentan nelimitat.
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Helmet>
        <title>Credite | mFirme</title>
        <meta name="description" content="Cumpără credite pentru a accesa informații despre firme" />
      </Helmet>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Înapoi
        </button>

        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold tracking-tight mb-2">Credite</h1>
          <p className="text-muted-foreground">
            Cumpără credite pentru a accesa informații detaliate despre firme
          </p>
        </div>

        {/* Current status */}
        <div className="grid sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-card border border-border rounded-xl p-5 text-center">
            <CreditCard className="w-8 h-8 mx-auto mb-2 text-primary" />
            <div className="text-3xl font-bold text-foreground">{creditsBalance}</div>
            <div className="text-sm text-muted-foreground">Credite disponibile</div>
          </div>
          
          <div className="bg-card border border-border rounded-xl p-5 text-center">
            <Calendar className="w-8 h-8 mx-auto mb-2 text-green-500" />
            <div className="text-3xl font-bold text-foreground">{freeViewsToday}/{freeViewsMax}</div>
            <div className="text-sm text-muted-foreground">Vizualizări gratuite azi</div>
          </div>
          
          <div className="bg-card border border-border rounded-xl p-5 text-center">
            <Eye className="w-8 h-8 mx-auto mb-2 text-blue-500" />
            <div className="text-3xl font-bold text-foreground">{totalViews}</div>
            <div className="text-sm text-muted-foreground">Total firme vizualizate</div>
          </div>
        </div>

        {/* How it works */}
        <div className="bg-secondary/50 rounded-xl p-6 mb-8">
          <h3 className="font-semibold mb-3">Cum funcționează?</h3>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Primești <strong>5 vizualizări gratuite</strong> în fiecare zi (se resetează la miezul nopții)</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>Firmele pe care le-ai vizualizat deja sunt <strong>gratuite</strong> - nu mai costă din nou</span>
            </li>
            <li className="flex items-start gap-2">
              <Check className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
              <span>După epuizarea vizualizărilor gratuite, fiecare firmă nouă costă <strong>1 credit</strong></span>
            </li>
          </ul>
        </div>

        {/* Packages */}
        <h3 className="font-semibold mb-4">Alege un pachet</h3>
        <div className="grid sm:grid-cols-3 gap-4">
          {packages.map((pkg) => (
            <div
              key={pkg.id}
              className={`relative bg-card border rounded-xl p-6 transition-all ${
                pkg.popular 
                  ? 'border-primary shadow-lg scale-105' 
                  : 'border-border hover:border-primary/50'
              }`}
            >
              {pkg.popular && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-primary text-primary-foreground text-xs font-medium rounded-full">
                  Cel mai popular
                </span>
              )}
              {pkg.best_value && (
                <span className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-green-500 text-white text-xs font-medium rounded-full">
                  Cel mai bun preț
                </span>
              )}

              <div className="flex items-center justify-center mb-4">
                {pkg.credits <= 50 && <Sparkles className="w-10 h-10 text-amber-500" />}
                {pkg.credits > 50 && pkg.credits <= 200 && <Zap className="w-10 h-10 text-primary" />}
                {pkg.credits > 200 && <CreditCard className="w-10 h-10 text-green-500" />}
              </div>

              <div className="text-center mb-4">
                <div className="text-3xl font-bold">{pkg.credits}</div>
                <div className="text-sm text-muted-foreground">credite</div>
              </div>

              <div className="text-center mb-4">
                <div className="text-2xl font-bold text-primary">{pkg.price} RON</div>
                <div className="text-xs text-muted-foreground">
                  {(pkg.price / pkg.credits).toFixed(2)} RON/credit
                </div>
              </div>

              <button
                onClick={() => handlePurchase(pkg.id)}
                disabled={loading}
                className={`w-full py-2.5 rounded-lg font-medium transition-colors ${
                  pkg.popular
                    ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                    : 'bg-secondary text-foreground hover:bg-secondary/80'
                } disabled:opacity-50`}
              >
                {loading && selectedPackage === pkg.id ? 'Se procesează...' : 'Cumpără'}
              </button>
            </div>
          ))}
        </div>

        {/* Payment info */}
        <div className="mt-8 text-center text-sm text-muted-foreground">
          <p>Plățile sunt procesate securizat prin Stripe</p>
          <p className="mt-1">Creditele nu expiră și pot fi folosite oricând</p>
        </div>
      </div>
    </>
  );
};

export default CreditsPage;
