import api from './api'; // Import the central API instance

const API_URL_PREFIX = process.env.REACT_APP_AC_API_URL || 'http://localhost:8001/api/v1';

/**
 * Public Consultation Service
 * 
 * Provides API communication for public consultation features including:
 * - Public proposal submission and retrieval
 * - Public feedback collection
 * - Consultation metrics and transparency data
 * - Integration with Constitutional Council workflows
 */
class PublicConsultationService {
    
    /**
     * Submit a new public proposal for constitutional consideration
     * @param {Object} proposalData - Proposal data object
     * @returns {Promise<Object>} Created proposal response
     */
    static async submitProposal(proposalData) {
        try {
            const response = await api.post(`${API_URL_PREFIX}/public-consultation/proposals`, proposalData);
            return response.data;
        } catch (error) {
            console.error('Failed to submit proposal:', error.response ? error.response.data : error.message);
            throw error.response ? error.response.data : new Error('Failed to submit proposal');
        }
    }
    
    /**
     * Get list of public proposals with optional filtering
     * @param {Object} filters - Optional filters (status, stakeholder_group, limit, offset)
     * @returns {Promise<Array>} Array of proposals
     */
    static async getProposals(filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.status) params.append('status', filters.status);
            if (filters.stakeholder_group) params.append('stakeholder_group', filters.stakeholder_group);
            if (filters.limit) params.append('limit', filters.limit);
            if (filters.offset) params.append('offset', filters.offset);
            
            const queryString = params.toString();
            const url = `${API_URL_PREFIX}/public-consultation/proposals${queryString ? `?${queryString}` : ''}`;
            
            const response = await api.get(url);
            return response.data;
        } catch (error) {
            console.error('Failed to fetch proposals:', error.response ? error.response.data : error.message);
            throw error.response ? error.response.data : new Error('Failed to fetch proposals');
        }
    }
    
    /**
     * Get detailed information about a specific proposal
     * @param {number} proposalId - ID of the proposal
     * @returns {Promise<Object>} Detailed proposal information
     */
    static async getProposal(proposalId) {
        try {
            const response = await api.get(`${API_URL_PREFIX}/public-consultation/proposals/${proposalId}`);
            return response.data;
        } catch (error) {
            console.error(`Failed to fetch proposal ${proposalId}:`, error.response ? error.response.data : error.message);
            throw error.response ? error.response.data : new Error('Failed to fetch proposal');
        }
    }
    
    /**
     * Submit public feedback on a proposal or amendment
     * @param {Object} feedbackData - Feedback data object
     * @returns {Promise<Object>} Created feedback response
     */
    static async submitFeedback(feedbackData) {
        try {
            const response = await api.post(`${API_URL_PREFIX}/public-consultation/feedback`, feedbackData);
            return response.data;
        } catch (error) {
            console.error('Failed to submit feedback:', error.response ? error.response.data : error.message);
            throw error.response ? error.response.data : new Error('Failed to submit feedback');
        }
    }
    
    /**
     * Get public feedback for a specific proposal
     * @param {number} proposalId - ID of the proposal
     * @param {Object} filters - Optional filters (feedback_type, limit, offset)
     * @returns {Promise<Array>} Array of feedback items
     */
    static async getProposalFeedback(proposalId, filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.feedback_type) params.append('feedback_type', filters.feedback_type);
            if (filters.limit) params.append('limit', filters.limit);
            if (filters.offset) params.append('offset', filters.offset);
            
            const queryString = params.toString();
            const url = `${API_URL_PREFIX}/public-consultation/feedback/${proposalId}${queryString ? `?${queryString}` : ''}`;
            
            const response = await api.get(url);
            return response.data;
        } catch (error) {
            console.error(`Failed to fetch feedback for proposal ${proposalId}:`, error.response ? error.response.data : error.message);
            throw error.response ? error.response.data : new Error('Failed to fetch feedback');
        }
    }
    
    /**
     * Get comprehensive consultation metrics for transparency
     * @param {number} timePeriodDays - Time period for metrics calculation (default: 30)
     * @returns {Promise<Object>} Consultation metrics
     */
    static async getMetrics(timePeriodDays = 30) {
        try {
            const response = await api.get(`${API_URL_PREFIX}/public-consultation/metrics?time_period_days=${timePeriodDays}`);
            return response.data;
        } catch (error) {
            console.error('Failed to fetch consultation metrics:', error.response ? error.response.data : error.message);
            throw error.response ? error.response.data : new Error('Failed to fetch metrics');
        }
    }
    
    /**
     * Get transparency dashboard data
     * @returns {Promise<Object>} Comprehensive transparency dashboard data
     */
    static async getTransparencyDashboard() {
        try {
            const response = await api.get(`${API_URL_PREFIX}/public-consultation/transparency-dashboard`);
            return response.data;
        } catch (error) {
            console.error('Failed to fetch transparency dashboard:', error.response ? error.response.data : error.message);
            throw error.response ? error.response.data : new Error('Failed to fetch dashboard data');
        }
    }
    
    /**
     * Advance a proposal to Constitutional Council consideration (requires special permissions)
     * @param {number} proposalId - ID of the proposal to advance
     * @returns {Promise<Object>} Advancement result
     */
    static async advanceProposalToCouncil(proposalId) {
        try {
            const response = await api.post(`${API_URL_PREFIX}/public-consultation/proposals/${proposalId}/advance`);
            return response.data;
        } catch (error) {
            console.error(`Failed to advance proposal ${proposalId}:`, error.response ? error.response.data : error.message);
            throw error.response ? error.response.data : new Error('Failed to advance proposal');
        }
    }
    
    /**
     * Get stakeholder group options for forms
     * @returns {Array} Array of stakeholder group options
     */
    static getStakeholderGroups() {
        return [
            { value: 'citizen', label: 'Citizen' },
            { value: 'expert', label: 'Expert' },
            { value: 'affected_party', label: 'Affected Party' },
            { value: 'regulatory_body', label: 'Regulatory Body' },
            { value: 'privacy_advocate', label: 'Privacy Advocate' },
            { value: 'security_expert', label: 'Security Expert' },
            { value: 'legal_expert', label: 'Legal Expert' },
            { value: 'civil_society', label: 'Civil Society' },
            { value: 'industry', label: 'Industry' },
            { value: 'academia', label: 'Academia' }
        ];
    }
    
    /**
     * Get feedback type options for forms
     * @returns {Array} Array of feedback type options
     */
    static getFeedbackTypes() {
        return [
            { value: 'support', label: 'Support' },
            { value: 'oppose', label: 'Oppose' },
            { value: 'neutral', label: 'Neutral' },
            { value: 'suggestion', label: 'Suggestion' },
            { value: 'concern', label: 'Concern' },
            { value: 'question', label: 'Question' }
        ];
    }
    
    /**
     * Get proposal status options for filtering
     * @returns {Array} Array of proposal status options
     */
    static getProposalStatuses() {
        return [
            { value: 'draft', label: 'Draft' },
            { value: 'open', label: 'Open for Consultation' },
            { value: 'active', label: 'Active' },
            { value: 'review', label: 'Under Review' },
            { value: 'closed', label: 'Closed' },
            { value: 'implemented', label: 'Implemented' }
        ];
    }
    
    /**
     * Validate proposal data before submission
     * @param {Object} proposalData - Proposal data to validate
     * @returns {Object} Validation result with isValid and errors
     */
    static validateProposal(proposalData) {
        const errors = [];
        
        if (!proposalData.title || proposalData.title.trim().length < 10) {
            errors.push('Title must be at least 10 characters long');
        }
        
        if (!proposalData.description || proposalData.description.trim().length < 50) {
            errors.push('Description must be at least 50 characters long');
        }
        
        if (!proposalData.proposed_changes || proposalData.proposed_changes.trim().length < 20) {
            errors.push('Proposed changes must be at least 20 characters long');
        }
        
        if (!proposalData.justification || proposalData.justification.trim().length < 20) {
            errors.push('Justification must be at least 20 characters long');
        }
        
        if (!proposalData.stakeholder_group) {
            errors.push('Stakeholder group is required');
        }
        
        if (proposalData.consultation_period_days && 
            (proposalData.consultation_period_days < 7 || proposalData.consultation_period_days > 90)) {
            errors.push('Consultation period must be between 7 and 90 days');
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    }
    
    /**
     * Validate feedback data before submission
     * @param {Object} feedbackData - Feedback data to validate
     * @returns {Object} Validation result with isValid and errors
     */
    static validateFeedback(feedbackData) {
        const errors = [];
        
        if (!feedbackData.proposal_id && !feedbackData.amendment_id) {
            errors.push('Either proposal ID or amendment ID is required');
        }
        
        if (!feedbackData.content || feedbackData.content.trim().length < 10) {
            errors.push('Feedback content must be at least 10 characters long');
        }
        
        if (feedbackData.content && feedbackData.content.length > 5000) {
            errors.push('Feedback content must not exceed 5000 characters');
        }
        
        if (!feedbackData.stakeholder_group) {
            errors.push('Stakeholder group is required');
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    }
    
    /**
     * Format date for display
     * @param {string} dateString - ISO date string
     * @returns {string} Formatted date string
     */
    static formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (error) {
            return 'Invalid date';
        }
    }
    
    /**
     * Calculate time remaining for consultation period
     * @param {string} createdAt - Creation date
     * @param {number} consultationPeriodDays - Consultation period in days
     * @returns {Object} Time remaining information
     */
    static getTimeRemaining(createdAt, consultationPeriodDays) {
        try {
            const created = new Date(createdAt);
            const endDate = new Date(created.getTime() + (consultationPeriodDays * 24 * 60 * 60 * 1000));
            const now = new Date();
            const timeRemaining = endDate.getTime() - now.getTime();
            
            if (timeRemaining <= 0) {
                return { expired: true, message: 'Consultation period has ended' };
            }
            
            const daysRemaining = Math.ceil(timeRemaining / (24 * 60 * 60 * 1000));
            
            return {
                expired: false,
                daysRemaining,
                message: `${daysRemaining} day${daysRemaining !== 1 ? 's' : ''} remaining`
            };
        } catch (error) {
            return { expired: true, message: 'Unable to calculate time remaining' };
        }
    }
}

export default PublicConsultationService;
