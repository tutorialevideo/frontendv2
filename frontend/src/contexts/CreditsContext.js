import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';

const CreditsContext = createContext(null);

export const useCredits = () => {
  const context = useContext(CreditsContext);
  if (!context) {
    throw new Error('useCredits must be used within a CreditsProvider');
  }
  return context;
};

export const CreditsProvider = ({ children }) => {
  const { isAuthenticated, token } = useAuth();
  const [credits, setCredits] = useState({
    systemEnabled: true,
    creditsBalance: 0,
    freeViewsToday: 0,
    freeViewsMax: 5,
    totalViews: 0,
    loading: true
  });
  const [showNoCreditsModal, setShowNoCreditsModal] = useState(false);

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  const fetchCreditsStatus = useCallback(async () => {
    if (!isAuthenticated || !token) {
      setCredits(prev => ({ ...prev, loading: false }));
      return;
    }

    try {
      const res = await fetch(`${API_URL}/api/credits/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setCredits({
          systemEnabled: data.system_enabled,
          creditsBalance: data.credits_balance,
          freeViewsToday: data.free_views_today,
          freeViewsMax: data.free_views_max,
          totalViews: data.total_views,
          loading: false
        });
      }
    } catch (error) {
      console.error('Failed to fetch credits status:', error);
      setCredits(prev => ({ ...prev, loading: false }));
    }
  }, [isAuthenticated, token, API_URL]);

  useEffect(() => {
    fetchCreditsStatus();
  }, [fetchCreditsStatus]);

  const checkAccess = async (companyCui) => {
    if (!credits.systemEnabled) {
      return { granted: true, reason: 'system_disabled' };
    }

    if (!isAuthenticated) {
      return { granted: false, reason: 'not_authenticated' };
    }

    try {
      const res = await fetch(`${API_URL}/api/credits/check-access`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ company_cui: companyCui })
      });

      const data = await res.json();
      
      if (!data.access_granted && data.reason === 'no_credits') {
        setShowNoCreditsModal(true);
      }

      return {
        granted: data.access_granted,
        reason: data.reason,
        willConsume: data.will_consume
      };
    } catch (error) {
      console.error('Failed to check access:', error);
      return { granted: true, reason: 'error' };
    }
  };

  const consumeCredit = async (companyCui) => {
    if (!credits.systemEnabled || !isAuthenticated) {
      return { consumed: false };
    }

    try {
      const res = await fetch(`${API_URL}/api/credits/consume`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ company_cui: companyCui })
      });

      if (res.ok) {
        const data = await res.json();
        
        // Update local state
        setCredits(prev => ({
          ...prev,
          creditsBalance: data.credits_balance,
          freeViewsToday: data.free_views_today,
          totalViews: prev.totalViews + (data.consumed ? 1 : 0)
        }));

        return {
          consumed: data.consumed,
          type: data.type,
          creditsBalance: data.credits_balance,
          freeViewsToday: data.free_views_today
        };
      } else if (res.status === 402) {
        setShowNoCreditsModal(true);
        return { consumed: false, reason: 'no_credits' };
      }
    } catch (error) {
      console.error('Failed to consume credit:', error);
    }

    return { consumed: false };
  };

  const refreshCredits = () => {
    fetchCreditsStatus();
  };

  const value = {
    ...credits,
    checkAccess,
    consumeCredit,
    refreshCredits,
    showNoCreditsModal,
    setShowNoCreditsModal
  };

  return (
    <CreditsContext.Provider value={value}>
      {children}
    </CreditsContext.Provider>
  );
};

export default CreditsContext;
