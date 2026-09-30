const apiOrigin = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

export const API = apiOrigin ? `${apiOrigin}/api` : '/api';
