import { useEffect } from 'react';
import { api } from '@/http/queryClient';

/**
 * Custom hook to load Umami analytics script after authentication
 * This ensures analytics only loads for authenticated users
 */
export const useAnalytics = (isAuthenticated: boolean) => {
  useEffect(() => {
    if (!isAuthenticated) return;

    let scriptElement: HTMLScriptElement | null = null;

    const loadAnalytics = async () => {
      try {
        const response = await api.get('/settings/get.umami.settings');
        const config = response.data;

        if (config.website_id && config.umami_url) {
          scriptElement = document.createElement('script');
          scriptElement.async = true;
          scriptElement.defer = true;
          scriptElement.setAttribute('data-website-id', config.website_id);
          scriptElement.src = `${config.umami_url}/script.js`;
          document.head.appendChild(scriptElement);
        }
      } catch (error) {
        console.warn('Failed to load analytics config:', error);
      }
    };

    loadAnalytics();

    // Cleanup function to remove script if component unmounts
    return () => {
      if (scriptElement && document.head.contains(scriptElement)) {
        document.head.removeChild(scriptElement);
      }
    };
  }, [isAuthenticated]);
};

