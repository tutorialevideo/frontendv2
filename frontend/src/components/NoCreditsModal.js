import React from 'react';
import { Link } from 'react-router-dom';
import { X, CreditCard, Sparkles, Zap } from 'lucide-react';
import { useCredits } from '../contexts/CreditsContext';

const NoCreditsModal = () => {
  const { showNoCreditsModal, setShowNoCreditsModal, creditsBalance, freeViewsToday } = useCredits();

  if (!showNoCreditsModal) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={() => setShowNoCreditsModal(false)}
      />
      
      {/* Modal */}
      <div className="relative bg-card border border-border rounded-2xl shadow-2xl max-w-md w-full mx-4 overflow-hidden">
        {/* Close button */}
        <button
          onClick={() => setShowNoCreditsModal(false)}
          className="absolute top-4 right-4 p-1 rounded-lg hover:bg-accent transition-colors"
        >
          <X className="w-5 h-5 text-muted-foreground" />
        </button>

        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-amber-500 to-orange-500 px-6 py-8 text-white">
          <div className="flex items-center justify-center mb-4">
            <div className="p-3 bg-white/20 rounded-full">
              <CreditCard className="w-8 h-8" />
            </div>
          </div>
          <h2 className="text-2xl font-bold text-center">Creditele s-au epuizat</h2>
          <p className="text-center text-white/80 mt-2">
            Ai folosit toate vizualizările gratuite de azi
          </p>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Current status */}
          <div className="flex justify-center gap-4 mb-6">
            <div className="text-center px-4 py-2 bg-secondary rounded-lg">
              <div className="text-2xl font-bold text-foreground">{creditsBalance}</div>
              <div className="text-xs text-muted-foreground">Credite</div>
            </div>
            <div className="text-center px-4 py-2 bg-secondary rounded-lg">
              <div className="text-2xl font-bold text-foreground">{freeViewsToday}</div>
              <div className="text-xs text-muted-foreground">Gratuite azi</div>
            </div>
          </div>

          {/* Packages preview */}
          <div className="space-y-3 mb-6">
            <div className="flex items-center justify-between p-3 border border-border rounded-lg hover:border-primary/50 transition-colors">
              <div className="flex items-center gap-3">
                <Sparkles className="w-5 h-5 text-amber-500" />
                <div>
                  <div className="font-medium">50 Credite</div>
                  <div className="text-xs text-muted-foreground">Pentru utilizare ocazională</div>
                </div>
              </div>
              <div className="text-lg font-bold text-primary">9.99 RON</div>
            </div>

            <div className="flex items-center justify-between p-3 border-2 border-primary rounded-lg bg-primary/5 relative">
              <span className="absolute -top-2 left-3 px-2 py-0.5 bg-primary text-primary-foreground text-xs font-medium rounded">
                Popular
              </span>
              <div className="flex items-center gap-3">
                <Zap className="w-5 h-5 text-primary" />
                <div>
                  <div className="font-medium">200 Credite</div>
                  <div className="text-xs text-muted-foreground">Cel mai cumpărat</div>
                </div>
              </div>
              <div className="text-lg font-bold text-primary">29.99 RON</div>
            </div>

            <div className="flex items-center justify-between p-3 border border-border rounded-lg hover:border-primary/50 transition-colors">
              <div className="flex items-center gap-3">
                <CreditCard className="w-5 h-5 text-green-500" />
                <div>
                  <div className="font-medium">500 Credite</div>
                  <div className="text-xs text-muted-foreground">Cel mai bun preț/credit</div>
                </div>
              </div>
              <div className="text-lg font-bold text-primary">59.99 RON</div>
            </div>
          </div>

          {/* CTA */}
          <Link
            to="/account/credits"
            onClick={() => setShowNoCreditsModal(false)}
            className="block w-full py-3 bg-primary text-primary-foreground text-center font-medium rounded-lg hover:bg-primary/90 transition-colors"
          >
            Cumpără credite
          </Link>

          <p className="text-center text-xs text-muted-foreground mt-4">
            Vizualizările gratuite se resetează zilnic la miezul nopții
          </p>
        </div>
      </div>
    </div>
  );
};

export default NoCreditsModal;
