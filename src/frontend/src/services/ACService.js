import api from './api'; // Import the central API instance

const API_URL_PREFIX = process.env.REACT_APP_AC_API_URL || 'http://localhost:8001/api/v1';

// No longer need getAuthHeaders as cookies and CSRF are handled by the api instance.

const getPrinciples = async () => {
    try {
        const response = await api.get(`${API_URL_PREFIX}/principles/`);
        return response.data; 
    } catch (error) {
        console.error('Failed to fetch principles:', error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error('Failed to fetch principles');
    }
};

const getPrincipleById = async (id) => {
    try {
        const response = await api.get(`${API_URL_PREFIX}/principles/${id}`);
        return response.data;
    } catch (error) {
        console.error(`Failed to fetch principle ${id}:`, error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error(`Failed to fetch principle ${id}`);
    }
};

const createPrinciple = async (principleData) => {
    try {
        const response = await api.post(`${API_URL_PREFIX}/principles/`, principleData);
        return response.data;
    } catch (error) {
        console.error('Failed to create principle:', error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error('Failed to create principle');
    }
};

const updatePrinciple = async (id, principleData) => {
    try {
        const response = await api.put(`${API_URL_PREFIX}/principles/${id}`, principleData);
        return response.data;
    } catch (error) {
        console.error(`Failed to update principle ${id}:`, error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error(`Failed to update principle ${id}`);
    }
};

const deletePrinciple = async (id) => {
    try {
        const response = await api.delete(`${API_URL_PREFIX}/principles/${id}`);
        return response.data; 
    } catch (error) {
        console.error(`Failed to delete principle ${id}:`, error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error(`Failed to delete principle ${id}`);
    }
};

const ACService = {
    getPrinciples,
    getPrincipleById,
    createPrinciple,
    updatePrinciple,
    deletePrinciple
};

export default ACService;
