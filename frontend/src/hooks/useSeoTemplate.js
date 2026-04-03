import { useState, useEffect, useCallback } from 'react';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';

// Cache pentru template-uri
let templateCache = null;
let cacheTimestamp = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minute

/**
 * Hook pentru a genera SEO metadata dinamic bazat pe template-uri din backend
 */
export const useSeoTemplate = (pageType, data = {}) => {
  const [seoData, setSeoData] = useState({
    title: '',
    description: '',
    index: true
  });
  const [loading, setLoading] = useState(true);

  const fetchTemplates = useCallback(async () => {
    // Verifică cache
    if (templateCache && cacheTimestamp && (Date.now() - cacheTimestamp) < CACHE_DURATION) {
      return templateCache;
    }

    try {
      const response = await fetch(`${API_URL}/api/seo/templates/public`);
      if (response.ok) {
        const text = await response.text();
        const result = text ? JSON.parse(text) : {};
        templateCache = result.templates || {};
        cacheTimestamp = Date.now();
        return templateCache;
      }
    } catch (err) {
      console.warn('Failed to fetch SEO templates:', err);
    }
    return null;
  }, []);

  const applyTemplate = useCallback((template, variables) => {
    if (!template) return '';
    
    let result = template;
    Object.entries(variables).forEach(([key, value]) => {
      const regex = new RegExp(`\\{${key}\\}`, 'g');
      result = result.replace(regex, value || '');
    });
    
    // Curăță variabile neînlocuite
    result = result.replace(/\{[A-Z_]+\}/g, '');
    
    return result.trim();
  }, []);

  useEffect(() => {
    const generateSeo = async () => {
      setLoading(true);
      
      const templates = await fetchTemplates();
      
      if (templates && templates[pageType]) {
        const template = templates[pageType];
        
        setSeoData({
          title: applyTemplate(template.title_template, data),
          description: applyTemplate(template.description_template, data),
          index: template.index !== false
        });
      } else {
        // Fallback dacă nu avem template
        setSeoData({
          title: data.DENUMIRE || 'RapoarteFirme.ro',
          description: '',
          index: true
        });
      }
      
      setLoading(false);
    };

    generateSeo();
  }, [pageType, JSON.stringify(data), fetchTemplates, applyTemplate]);

  return { ...seoData, loading };
};

/**
 * Preîncarcă template-urile (util la startup)
 */
export const preloadSeoTemplates = async () => {
  try {
    const response = await fetch(`${API_URL}/api/seo/templates/public`);
    if (response.ok) {
      const text = await response.text();
      const result = text ? JSON.parse(text) : {};
      templateCache = result.templates || {};
      cacheTimestamp = Date.now();
    }
  } catch (err) {
    console.warn('Failed to preload SEO templates:', err);
  }
};

/**
 * Invalidează cache-ul (util după ce admin modifică template-uri)
 */
export const invalidateSeoCache = () => {
  templateCache = null;
  cacheTimestamp = null;
};

export default useSeoTemplate;
