import api from './api'; // Import the central API instance

const API_URL_PREFIX = process.env.REACT_APP_GS_API_URL || 'http://localhost:8003/api/v1';

// No longer need getAuthHeaders as cookies and CSRF are handled by the api instance.

const synthesizePolicies = async (synthesisRequestData) => {
    try {
        const response = await api.post(`${API_URL_PREFIX}/synthesize/`, synthesisRequestData);
        return response.data;
    } catch (error) {
        console.error('Failed to synthesize policies:', error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error('Failed to synthesize policies');
    }
};

const GSService = {
    synthesizePolicies
};

export default GSService;
