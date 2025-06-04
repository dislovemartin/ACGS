import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../../contexts/AuthContext';
import PublicConsultationService from '../../services/PublicConsultationService';
import './PublicConsultationPage.css';

const PublicConsultationPage = () => {
    const { currentUser } = useContext(AuthContext);
    const [activeTab, setActiveTab] = useState('proposals');
    const [proposals, setProposals] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    
    // Form states
    const [showProposalForm, setShowProposalForm] = useState(false);
    const [proposalForm, setProposalForm] = useState({
        title: '',
        description: '',
        proposed_changes: '',
        justification: '',
        submitter_name: '',
        submitter_email: '',
        submitter_organization: '',
        stakeholder_group: 'citizen',
        consultation_period_days: 30
    });
    
    const [feedbackForm, setFeedbackForm] = useState({
        proposal_id: null,
        feedback_type: 'neutral',
        content: '',
        submitter_name: '',
        submitter_email: '',
        stakeholder_group: 'citizen'
    });

    useEffect(() => {
        loadProposals();
        loadMetrics();
    }, []);

    const loadProposals = async () => {
        try {
            setLoading(true);
            const data = await PublicConsultationService.getProposals();
            setProposals(data);
        } catch (err) {
            setError('Failed to load proposals');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const loadMetrics = async () => {
        try {
            const data = await PublicConsultationService.getMetrics();
            setMetrics(data);
        } catch (err) {
            console.error('Failed to load metrics:', err);
        }
    };

    const handleSubmitProposal = async (e) => {
        e.preventDefault();
        try {
            setLoading(true);
            await PublicConsultationService.submitProposal(proposalForm);
            setShowProposalForm(false);
            setProposalForm({
                title: '',
                description: '',
                proposed_changes: '',
                justification: '',
                submitter_name: '',
                submitter_email: '',
                submitter_organization: '',
                stakeholder_group: 'citizen',
                consultation_period_days: 30
            });
            await loadProposals();
            alert('Proposal submitted successfully!');
        } catch (err) {
            setError('Failed to submit proposal');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmitFeedback = async (e) => {
        e.preventDefault();
        try {
            setLoading(true);
            await PublicConsultationService.submitFeedback(feedbackForm);
            setFeedbackForm({
                proposal_id: null,
                feedback_type: 'neutral',
                content: '',
                submitter_name: '',
                submitter_email: '',
                stakeholder_group: 'citizen'
            });
            alert('Feedback submitted successfully!');
        } catch (err) {
            setError('Failed to submit feedback');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const renderProposals = () => (
        <div className="proposals-section">
            <div className="section-header">
                <h3>Constitutional Proposals</h3>
                <button 
                    className="btn btn-primary"
                    onClick={() => setShowProposalForm(true)}
                >
                    Submit New Proposal
                </button>
            </div>
            
            {loading && <div className="loading">Loading proposals...</div>}
            {error && <div className="error">{error}</div>}
            
            <div className="proposals-grid">
                {proposals.map(proposal => (
                    <div key={proposal.id} className="proposal-card">
                        <div className="proposal-header">
                            <h4>{proposal.title}</h4>
                            <span className={`status-badge status-${proposal.status}`}>
                                {proposal.status}
                            </span>
                        </div>
                        <p className="proposal-description">{proposal.description}</p>
                        <div className="proposal-meta">
                            <span>By: {proposal.submitter_name || 'Anonymous'}</span>
                            <span>Support: {proposal.public_support_count}</span>
                            <span>Group: {proposal.stakeholder_group}</span>
                        </div>
                        <div className="proposal-actions">
                            <button 
                                className="btn btn-sm btn-outline"
                                onClick={() => {
                                    setFeedbackForm({...feedbackForm, proposal_id: proposal.id});
                                    setActiveTab('feedback');
                                }}
                            >
                                Provide Feedback
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    const renderFeedbackForm = () => (
        <div className="feedback-section">
            <h3>Submit Public Feedback</h3>
            <form onSubmit={handleSubmitFeedback} className="feedback-form">
                <div className="form-group">
                    <label>Proposal</label>
                    <select 
                        value={feedbackForm.proposal_id || ''}
                        onChange={(e) => setFeedbackForm({...feedbackForm, proposal_id: parseInt(e.target.value)})}
                        required
                    >
                        <option value="">Select a proposal</option>
                        {proposals.map(proposal => (
                            <option key={proposal.id} value={proposal.id}>
                                {proposal.title}
                            </option>
                        ))}
                    </select>
                </div>
                
                <div className="form-group">
                    <label>Feedback Type</label>
                    <select 
                        value={feedbackForm.feedback_type}
                        onChange={(e) => setFeedbackForm({...feedbackForm, feedback_type: e.target.value})}
                    >
                        <option value="support">Support</option>
                        <option value="oppose">Oppose</option>
                        <option value="neutral">Neutral</option>
                        <option value="suggestion">Suggestion</option>
                        <option value="concern">Concern</option>
                        <option value="question">Question</option>
                    </select>
                </div>
                
                <div className="form-group">
                    <label>Your Feedback</label>
                    <textarea 
                        value={feedbackForm.content}
                        onChange={(e) => setFeedbackForm({...feedbackForm, content: e.target.value})}
                        placeholder="Share your thoughts on this proposal..."
                        rows="6"
                        required
                    />
                </div>
                
                <div className="form-row">
                    <div className="form-group">
                        <label>Your Name (Optional)</label>
                        <input 
                            type="text"
                            value={feedbackForm.submitter_name}
                            onChange={(e) => setFeedbackForm({...feedbackForm, submitter_name: e.target.value})}
                            placeholder="Your name"
                        />
                    </div>
                    <div className="form-group">
                        <label>Email (Optional)</label>
                        <input 
                            type="email"
                            value={feedbackForm.submitter_email}
                            onChange={(e) => setFeedbackForm({...feedbackForm, submitter_email: e.target.value})}
                            placeholder="your@email.com"
                        />
                    </div>
                </div>
                
                <div className="form-group">
                    <label>Stakeholder Group</label>
                    <select 
                        value={feedbackForm.stakeholder_group}
                        onChange={(e) => setFeedbackForm({...feedbackForm, stakeholder_group: e.target.value})}
                    >
                        <option value="citizen">Citizen</option>
                        <option value="expert">Expert</option>
                        <option value="affected_party">Affected Party</option>
                        <option value="privacy_advocate">Privacy Advocate</option>
                        <option value="security_expert">Security Expert</option>
                        <option value="legal_expert">Legal Expert</option>
                        <option value="civil_society">Civil Society</option>
                        <option value="industry">Industry</option>
                        <option value="academia">Academia</option>
                    </select>
                </div>
                
                <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Submitting...' : 'Submit Feedback'}
                </button>
            </form>
        </div>
    );

    const renderMetrics = () => (
        <div className="metrics-section">
            <h3>Public Consultation Transparency</h3>
            {metrics && (
                <div className="metrics-grid">
                    <div className="metric-card">
                        <h4>{metrics.total_proposals}</h4>
                        <p>Total Proposals</p>
                    </div>
                    <div className="metric-card">
                        <h4>{metrics.active_consultations}</h4>
                        <p>Active Consultations</p>
                    </div>
                    <div className="metric-card">
                        <h4>{metrics.total_participants}</h4>
                        <p>Total Participants</p>
                    </div>
                    <div className="metric-card">
                        <h4>{metrics.feedback_count}</h4>
                        <p>Feedback Items</p>
                    </div>
                    <div className="metric-card">
                        <h4>{(metrics.engagement_rate * 100).toFixed(1)}%</h4>
                        <p>Engagement Rate</p>
                    </div>
                    <div className="metric-card">
                        <h4>{(metrics.completion_rate * 100).toFixed(1)}%</h4>
                        <p>Completion Rate</p>
                    </div>
                </div>
            )}
            
            {metrics && metrics.sentiment_distribution && (
                <div className="sentiment-chart">
                    <h4>Public Sentiment Distribution</h4>
                    <div className="sentiment-bars">
                        <div className="sentiment-bar">
                            <span>Positive</span>
                            <div className="bar">
                                <div 
                                    className="bar-fill positive" 
                                    style={{width: `${metrics.sentiment_distribution.positive}%`}}
                                ></div>
                            </div>
                            <span>{metrics.sentiment_distribution.positive}%</span>
                        </div>
                        <div className="sentiment-bar">
                            <span>Neutral</span>
                            <div className="bar">
                                <div 
                                    className="bar-fill neutral" 
                                    style={{width: `${metrics.sentiment_distribution.neutral}%`}}
                                ></div>
                            </div>
                            <span>{metrics.sentiment_distribution.neutral}%</span>
                        </div>
                        <div className="sentiment-bar">
                            <span>Negative</span>
                            <div className="bar">
                                <div 
                                    className="bar-fill negative" 
                                    style={{width: `${metrics.sentiment_distribution.negative}%`}}
                                ></div>
                            </div>
                            <span>{metrics.sentiment_distribution.negative}%</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );

    const renderProposalForm = () => (
        <div className="modal-overlay" onClick={() => setShowProposalForm(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h3>Submit Constitutional Proposal</h3>
                    <button 
                        className="close-btn"
                        onClick={() => setShowProposalForm(false)}
                    >
                        ×
                    </button>
                </div>
                <form onSubmit={handleSubmitProposal} className="proposal-form">
                    <div className="form-group">
                        <label>Proposal Title *</label>
                        <input 
                            type="text"
                            value={proposalForm.title}
                            onChange={(e) => setProposalForm({...proposalForm, title: e.target.value})}
                            placeholder="Brief, descriptive title for your proposal"
                            required
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>Description *</label>
                        <textarea 
                            value={proposalForm.description}
                            onChange={(e) => setProposalForm({...proposalForm, description: e.target.value})}
                            placeholder="Detailed description of your proposal..."
                            rows="4"
                            required
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>Proposed Changes *</label>
                        <textarea 
                            value={proposalForm.proposed_changes}
                            onChange={(e) => setProposalForm({...proposalForm, proposed_changes: e.target.value})}
                            placeholder="Specific changes you are proposing..."
                            rows="4"
                            required
                        />
                    </div>
                    
                    <div className="form-group">
                        <label>Justification *</label>
                        <textarea 
                            value={proposalForm.justification}
                            onChange={(e) => setProposalForm({...proposalForm, justification: e.target.value})}
                            placeholder="Why is this change necessary?"
                            rows="3"
                            required
                        />
                    </div>
                    
                    <div className="form-row">
                        <div className="form-group">
                            <label>Your Name</label>
                            <input 
                                type="text"
                                value={proposalForm.submitter_name}
                                onChange={(e) => setProposalForm({...proposalForm, submitter_name: e.target.value})}
                                placeholder="Your name"
                            />
                        </div>
                        <div className="form-group">
                            <label>Email</label>
                            <input 
                                type="email"
                                value={proposalForm.submitter_email}
                                onChange={(e) => setProposalForm({...proposalForm, submitter_email: e.target.value})}
                                placeholder="your@email.com"
                            />
                        </div>
                    </div>
                    
                    <div className="form-row">
                        <div className="form-group">
                            <label>Organization</label>
                            <input 
                                type="text"
                                value={proposalForm.submitter_organization}
                                onChange={(e) => setProposalForm({...proposalForm, submitter_organization: e.target.value})}
                                placeholder="Your organization (optional)"
                            />
                        </div>
                        <div className="form-group">
                            <label>Stakeholder Group</label>
                            <select 
                                value={proposalForm.stakeholder_group}
                                onChange={(e) => setProposalForm({...proposalForm, stakeholder_group: e.target.value})}
                            >
                                <option value="citizen">Citizen</option>
                                <option value="expert">Expert</option>
                                <option value="privacy_advocate">Privacy Advocate</option>
                                <option value="security_expert">Security Expert</option>
                                <option value="legal_expert">Legal Expert</option>
                                <option value="civil_society">Civil Society</option>
                                <option value="industry">Industry</option>
                                <option value="academia">Academia</option>
                            </select>
                        </div>
                    </div>
                    
                    <div className="form-actions">
                        <button 
                            type="button" 
                            className="btn btn-secondary"
                            onClick={() => setShowProposalForm(false)}
                        >
                            Cancel
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? 'Submitting...' : 'Submit Proposal'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );

    return (
        <div className="public-consultation-page">
            <div className="page-header">
                <h1>Public Consultation</h1>
                <p>Participate in constitutional governance through democratic consultation</p>
            </div>
            
            <div className="tab-navigation">
                <button 
                    className={`tab-btn ${activeTab === 'proposals' ? 'active' : ''}`}
                    onClick={() => setActiveTab('proposals')}
                >
                    Proposals
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'feedback' ? 'active' : ''}`}
                    onClick={() => setActiveTab('feedback')}
                >
                    Submit Feedback
                </button>
                <button 
                    className={`tab-btn ${activeTab === 'transparency' ? 'active' : ''}`}
                    onClick={() => setActiveTab('transparency')}
                >
                    Transparency Dashboard
                </button>
            </div>
            
            <div className="tab-content">
                {activeTab === 'proposals' && renderProposals()}
                {activeTab === 'feedback' && renderFeedbackForm()}
                {activeTab === 'transparency' && renderMetrics()}
            </div>
            
            {showProposalForm && renderProposalForm()}
        </div>
    );
};

export default PublicConsultationPage;
