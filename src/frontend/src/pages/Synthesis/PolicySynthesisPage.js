import React, { useState, useEffect, useCallback, useContext } from 'react';
import ACService from '../../services/ACService'; // To fetch principles
import GSService from '../../services/GSService'; // To trigger synthesis
import { AuthContext } from '../../contexts/AuthContext';

const PolicySynthesisPage = () => {
    const [availablePrinciples, setAvailablePrinciples] = useState([]);
    const [selectedPrincipleIds, setSelectedPrincipleIds] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [synthesisResult, setSynthesisResult] = useState(null);
    const [error, setError] = useState('');
    const { currentUser } = useContext(AuthContext);

    const fetchAvailablePrinciples = useCallback(async () => {
        if (!currentUser) return;
        setIsLoading(true);
        try {
            const data = await ACService.getPrinciples(); // Assuming this returns { principles: [...] }
            setAvailablePrinciples(data.principles || []);
        } catch (err) {
            setError(err.message || 'Failed to fetch AC principles.');
        } finally {
            setIsLoading(false);
        }
    }, [currentUser]);

    useEffect(() => {
        fetchAvailablePrinciples();
    }, [fetchAvailablePrinciples]);

    const handlePrincipleSelectionChange = (e) => {
        const { value, checked } = e.target;
        const principleId = parseInt(value, 10);
        setSelectedPrincipleIds(prev =>
            checked ? [...prev, principleId] : prev.filter(id => id !== principleId)
        );
    };

    const handleSynthesize = async () => {
        if (selectedPrincipleIds.length === 0) {
            setError('Please select at least one principle to synthesize.');
            return;
        }
        setIsLoading(true);
        setError('');
        setSynthesisResult(null);
        try {
            const requestData = {
                principles: selectedPrincipleIds.map(id => ({ id }))
                // target_context: "some_context" // If you add context input
            };
            const result = await GSService.synthesizePolicies(requestData);
            setSynthesisResult(result);
        } catch (err) {
            setError(err.message || 'Policy synthesis failed.');
        } finally {
            setIsLoading(false);
        }
    };

    if (!currentUser) {
        return <p>Please login to access policy synthesis features.</p>;
    }

    return (
        <div>
            <h2>Policy Synthesis</h2>
            
            <h3>Select AC Principles:</h3>
            {isLoading && availablePrinciples.length === 0 && <p>Loading principles...</p>}
            {error && <p style={{ color: 'red' }}>{error}</p>}
            
            <div style={{ maxHeight: '200px', overflowY: 'auto', border: '1px solid #ccc', marginBottom: '10px' }}>
                {availablePrinciples.map(p => (
                    <div key={p.id}>
                        <input
                            type="checkbox"
                            id={`principle-${p.id}`}
                            value={p.id}
                            onChange={handlePrincipleSelectionChange}
                            checked={selectedPrincipleIds.includes(p.id)}
                        />
                        <label htmlFor={`principle-${p.id}`}>{p.name} (ID: {p.id})</label>
                    </div>
                ))}
            </div>

            <button onClick={handleSynthesize} disabled={isLoading || selectedPrincipleIds.length === 0}>
                {isLoading ? 'Synthesizing...' : 'Synthesize Policies'}
            </button>

            {synthesisResult && (
                <div style={{ marginTop: '20px', border: '1px solid #eee', padding: '10px' }}>
                    <h3>Synthesis Results:</h3>
                    <p><strong>Overall Status:</strong> {synthesisResult.overall_synthesis_status}</p>
                    <p><strong>Message:</strong> {synthesisResult.message}</p>
                    <h4>Generated Rules:</h4>
                    {synthesisResult.generated_rules && synthesisResult.generated_rules.length > 0 ? (
                        <ul style={{ listStyleType: 'none', padding: 0 }}>
                            {synthesisResult.generated_rules.map((rule, index) => (
                                <li key={rule.stored_rule_id || `rule-${index}`} style={{ border: '1px solid #ddd', margin: '5px', padding: '5px' }}>
                                    <p><strong>Stored Rule ID:</strong> {rule.stored_rule_id || 'N/A (Not Stored)'}</p>
                                    <p><strong>Content:</strong> <pre style={{ whiteSpace: 'pre-wrap', background: '#f9f9f9' }}>{rule.rule_content}</pre></p>
                                    <p><strong>Source Principle IDs:</strong> {rule.source_principle_ids.join(', ')}</p>
                                    <p><strong>Verification Status:</strong> <span style={{ fontWeight: 'bold', color: rule.verification_status === 'verified' ? 'green' : (rule.verification_status === 'failed' ? 'red' : 'orange') }}>{rule.verification_status || 'N/A'}</span></p>
                                    {rule.verification_feedback && <p><strong>Feedback:</strong> {rule.verification_feedback}</p>}
                                </li>
                            ))}
                        </ul>
                    ) : <p>No rules were generated or included in the result.</p>}
                </div>
            )}
        </div>
    );
};

export default PolicySynthesisPage;
