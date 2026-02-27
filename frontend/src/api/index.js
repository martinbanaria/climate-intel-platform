import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Market Items API
export const marketAPI = {
    getAll: async (params = {}) => {
        try {
            const response = await axios.get(`${API}/market-items`, { params });
            return response.data;
        } catch (error) {
            console.error('Error fetching market items:', error);
            throw error;
        }
    },
    
    getById: async (id) => {
        try {
            const response = await axios.get(`${API}/market-items/${id}`);
            return response.data;
        } catch (error) {
            console.error('Error fetching market item:', error);
            throw error;
        }
    },
    
    getBestDeals: async (limit = 8) => {
        try {
            const response = await axios.get(`${API}/best-deals`, { params: { limit } });
            return response.data;
        } catch (error) {
            console.error('Error fetching best deals:', error);
            throw error;
        }
    }
};

// Climate Metrics API
export const climateAPI = {
    getAll: async () => {
        try {
            const response = await axios.get(`${API}/climate-metrics`);
            return response.data;
        } catch (error) {
            console.error('Error fetching climate metrics:', error);
            throw error;
        }
    },
    
    getById: async (id) => {
        try {
            const response = await axios.get(`${API}/climate-metrics/${id}`);
            return response.data;
        } catch (error) {
            console.error('Error fetching climate metric:', error);
            throw error;
        }
    }
};

// Categories API
export const categoryAPI = {
    getAll: async () => {
        try {
            const response = await axios.get(`${API}/categories`);
            return response.data;
        } catch (error) {
            console.error('Error fetching categories:', error);
            throw error;
        }
    }
};

// Analytics API
export const analyticsAPI = {
    getMarketAnalytics: async () => {
        try {
            const response = await axios.get(`${API}/analytics/market-analytics`);
            return response.data;
        } catch (error) {
            console.error('Error fetching market analytics:', error);
            throw error;
        }
    },
    
    getPriceTrends: async () => {
        try {
            const response = await axios.get(`${API}/analytics/price-trends`);
            return response.data;
        } catch (error) {
            console.error('Error fetching price trends:', error);
            throw error;
        }
    },
    
    getClimateCorrelations: async () => {
        try {
            const response = await axios.get(`${API}/analytics/climate-correlations`);
            return response.data;
        } catch (error) {
            console.error('Error fetching climate correlations:', error);
            throw error;
        }
    },
    
    getBuyingOpportunities: async () => {
        try {
            const response = await axios.get(`${API}/analytics/buying-opportunities`);
            return response.data;
        } catch (error) {
            console.error('Error fetching buying opportunities:', error);
            throw error;
        }
    },
    
    getWeeklyReport: async () => {
        try {
            const response = await axios.get(`${API}/analytics/weekly-report`);
            return response.data;
        } catch (error) {
            console.error('Error fetching weekly report:', error);
            throw error;
        }
    }
};

// Energy API
export const energyAPI = {
    getNews: async (query = 'renewable energy') => {
        try {
            const response = await axios.get(`${API}/energy/news`, { params: { query } });
            return response.data;
        } catch (error) {
            console.error('Error fetching energy news:', error);
            throw error;
        }
    },
    
    getGridStatus: async () => {
        try {
            const response = await axios.get(`${API}/energy/grid-status`);
            return response.data;
        } catch (error) {
            console.error('Error fetching grid status:', error);
            throw error;
        }
    },
    
    getPPAStatuses: async () => {
        try {
            const response = await axios.get(`${API}/energy/ppa-status`);
            return response.data;
        } catch (error) {
            console.error('Error fetching PPA statuses:', error);
            throw error;
        }
    },
    
    getDOECirculars: async () => {
        try {
            const response = await axios.get(`${API}/energy/doe-circulars`);
            return response.data;
        } catch (error) {
            console.error('Error fetching DOE circulars:', error);
            throw error;
        }
    },
    
    getAnalytics: async () => {
        try {
            const response = await axios.get(`${API}/energy/analytics`);
            return response.data;
        } catch (error) {
            console.error('Error fetching energy analytics:', error);
            throw error;
        }
    }
};

// Integration API
export const integrationAPI = {
    runComprehensiveIntegration: async (days = 7) => {
        try {
            const response = await axios.post(`${API}/integration/run-comprehensive-real-data?days=${days}`);
            return response.data;
        } catch (error) {
            console.error('Error running integration:', error);
            throw error;
        }
    },
    
    getStatus: async () => {
        try {
            const response = await axios.get(`${API}/integration/status`);
            return response.data;
        } catch (error) {
            console.error('Error fetching integration status:', error);
            throw error;
        }
    }
};

export default {
    market: marketAPI,
    climate: climateAPI,
    categories: categoryAPI,
    analytics: analyticsAPI,
    energy: energyAPI,
    integration: integrationAPI
};
