import api from './api'; // Import the central API instance

const API_URL_PREFIX = process.env.REACT_APP_INTEGRITY_API_URL || 'http://localhost:8006/api/v1';

// No longer need getAuthHeaders

const getPolicies = async (status = null) => {
    try {
        const params = {};
        if (status) {
            params.status = status;
        }
        const response = await api.get(`${API_URL_PREFIX}/policies/`, { params });
        return response.data; 
    } catch (error) {
        console.error('Failed to fetch policies:', error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error('Failed to fetch policies');
    }
};

const getPolicyById = async (id) => {
    try {
        const response = await api.get(`${API_URL_PREFIX}/policies/${id}`);
        return response.data;
    } catch (error) {
        console.error(`Failed to fetch policy ${id}:`, error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error(`Failed to fetch policy ${id}`);
    }
};

const getAuditLogs = async (params = {}) => {
    try {
        const response = await api.get(`${API_URL_PREFIX}/audit/`, { params });
        return response.data; 
    } catch (error) {
        console.error('Failed to fetch audit logs:', error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error('Failed to fetch audit logs');
    }
};

const IntegrityService = {
    getPolicies,
    getPolicyById,
    getAuditLogs 
};

export default IntegrityService;
